# -*- coding: utf-8 -*-
"""从币安公开 API 拉取 BTCUSDC/ETHUSDC 日线, 写成回测引擎的 codebased CSV 格式.

目录: data/market/kline/codebased/global_cryptospot/1d/{year}/{symbol}.csv
CSV 无表头, 列: time, code, open, high, low, close, volume, amount
time 为 UTC 日期 00:00:00 (与 market_context 中 cryptospot tz=UTC 一致).
同时生成 reference 股票列表与 runtime/constant.py.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKET = 'global_cryptospot'
SYMBOLS = [('BTCUSDC', 'Bitcoin'), ('ETHUSDC', 'Ethereum')]
HOSTS = ['https://api.binance.com', 'https://data-api.binance.vision']
START_MS = int(datetime(2017, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
LIMIT = 1000

kline_root = os.path.join(BASE_DIR, 'data', 'market', 'kline', 'codebased', MARKET, '1d')
ref_dir = os.path.join(BASE_DIR, 'data', 'market', 'reference', MARKET)


def api_get(path, params):
    qs = urllib.parse.urlencode(params)
    last_err = None
    for host in HOSTS:
        url = f'{host}{path}?{qs}'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'finhack-crypto-fetch/1.0'})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            last_err = e
            print(f'  [warn] {host} failed: {e}')
    raise RuntimeError(f'all hosts failed: {last_err}')


def fetch_symbol(symbol):
    rows = []
    start = START_MS
    while True:
        batch = api_get('/api/v3/klines', {
            'symbol': symbol, 'interval': '1d',
            'startTime': start, 'limit': LIMIT})
        if not batch:
            break
        rows.extend(batch)
        last_open = batch[-1][0]
        if len(batch) < LIMIT:
            break
        start = last_open + 1
        time.sleep(0.15)
    return rows


def write_csvs(symbol, rows):
    by_year = {}
    for k in rows:
        open_ms, o, h, l, c, vol, _close_ms, quote_vol = k[0], k[1], k[2], k[3], k[4], k[5], k[6], k[7]
        dt = datetime.fromtimestamp(open_ms / 1000, tz=timezone.utc)
        t = dt.strftime('%Y-%m-%d %H:%M:%S')
        by_year.setdefault(dt.year, []).append(
            f'{t},{symbol},{o},{h},{l},{c},{vol},{quote_vol}\n')
    n = 0
    for year, lines in sorted(by_year.items()):
        ydir = os.path.join(kline_root, str(year))
        os.makedirs(ydir, exist_ok=True)
        with open(os.path.join(ydir, f'{symbol}.csv'), 'w', encoding='utf-8', newline='') as f:
            f.writelines(lines)
        n += len(lines)
    return n


def main():
    os.makedirs(ref_dir, exist_ok=True)
    list_lines = ['code,display_name,name\n']
    for symbol, name in SYMBOLS:
        print(f'fetching {symbol} ...')
        rows = fetch_symbol(symbol)
        if not rows:
            print(f'  [error] {symbol}: no data returned')
            continue
        first = datetime.fromtimestamp(rows[0][0] / 1000, tz=timezone.utc)
        last = datetime.fromtimestamp(rows[-1][0] / 1000, tz=timezone.utc)
        count = write_csvs(symbol, rows)
        print(f'  {symbol}: {count} daily bars, {first:%Y-%m-%d} ~ {last:%Y-%m-%d}')
        list_lines.append(f'{symbol},{name},{name}\n')
    with open(os.path.join(ref_dir, f'{MARKET}_list.csv'), 'w', encoding='utf-8', newline='') as f:
        f.writelines(list_lines)
    print('list file written')

    rt = os.path.join(BASE_DIR, 'runtime')
    os.makedirs(rt, exist_ok=True)
    if not os.path.exists(os.path.join(rt, '__init__.py')):
        open(os.path.join(rt, '__init__.py'), 'w').close()
    if not os.path.exists(os.path.join(rt, 'constant.py')):
        with open(os.path.join(rt, 'constant.py'), 'w', encoding='utf-8') as f:
            f.write('import os\n\n'
                    'BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\n'
                    'DATA_DIR = os.path.join(BASE_DIR, "data")\n')
        print('runtime/constant.py written')
    else:
        print('runtime/constant.py exists, skipped')


if __name__ == '__main__':
    main()
