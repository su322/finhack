# -*- coding: utf-8 -*-
"""单币种策略矩阵回测: 多策略 x 多币种, 输出全期收益 + 分年度收益对比.

用法: python script/run_crypto_backtest.py [策略名...]
"""
import sys
import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

from types import SimpleNamespace
from finhack.trader.backtest import BacktestTrader

STRATEGIES = ['buy_hold', 'ma200', 'tsm30', 'donchian', 'tsm_vol']
SYMBOLS = ['BTCUSDC', 'ETHUSDC']
START, END, CASH = '2018-12-15', '2026-09-08', 10000.0
CURRENT_YEAR = 2026  # 未满一年, 表格中标注*


def make_args(strategy, symbol):
    return SimpleNamespace(
        market='global_cryptospot', freq='1d',
        start_time=START, end_time=END,
        cash=CASH, benchmark=symbol, strategy=strategy,
        universe=[symbol], params=json.dumps({'symbol': symbol}), model_id='',
        vendor='backtest', _cmdline_args={},
    )


def run_one(strategy, symbol):
    trader = BacktestTrader(make_args(strategy, symbol))
    trader.run()
    perf = trader.context.get('performance', {}) or {}
    ind = perf.get('indicators') or {}
    dh = trader.context.get('logs', {}).get('daily_history') or []
    curve = []
    for d in dh:
        try:
            curve.append((str(d.get('date'))[:10], float(d.get('total_assets'))))
        except (TypeError, ValueError):
            pass
    return {
        'strategy': strategy, 'symbol': symbol, 'curve': curve,
        'total': ind.get('total_return'), 'annual': ind.get('annual_return'),
        'mdd': ind.get('max_drawdown'), 'sharpe': ind.get('sharpe_ratio'),
        'trades': perf.get('trade_num'),
    }


def yearly_returns(curve):
    """按日历年度切分资产曲线 -> {year: return}."""
    if not curve:
        return {}
    by_year = {}
    for d, v in curve:
        by_year.setdefault(int(d[:4]), []).append((d, v))
    years = sorted(by_year)
    out = {}
    prev_end = curve[0][1]  # 起点(首年按曲线首值折算)
    for y in years:
        pts = by_year[y]
        end_v = pts[-1][1]
        out[y] = end_v / prev_end - 1 if prev_end > 0 else None
        prev_end = end_v
    return out


def fmt_pct(x):
    return f'{x * 100:7.1f}%' if isinstance(x, (int, float)) else '    N/A'


def main():
    strategies = sys.argv[1:] or STRATEGIES
    rows = []
    for strategy in strategies:
        for symbol in SYMBOLS:
            print(f'\n########## RUN {strategy} @ {symbol} ##########', flush=True)
            rows.append(run_one(strategy, symbol))

    years = list(range(2019, CURRENT_YEAR + 1))
    out = []
    out.append('# BTCUSDC/ETHUSDC 策略回测报告')
    out.append('')
    out.append(f'- 生成时间: {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")}')
    out.append(f'- 区间: {START} ~ {END}   初始: {CASH:,.0f} USD   手续费 0.1%/边   滑点 0.05%')
    out.append('- 数据: 币安现货日线 (UTC), 单币种全仓, 信号与成交均在当日收盘')
    out.append('')
    out.append('## 全期收益对比')
    out.append('')
    out.append(f'| 币种 | 策略 | 期末资产 | 累计收益 | 年化 | 最大回撤 | 夏普 | 交易次数 |')
    out.append(f'|---|---|---|---|---|---|---|---|')
    by_symbol = {}
    for r in rows:
        by_symbol.setdefault(r['symbol'], []).append(r)
    for symbol in SYMBOLS:
        for r in by_symbol.get(symbol, []):
            final = f'{r["curve"][-1][1]:,.0f}' if r['curve'] else 'N/A'
            sharpe = f'{r["sharpe"]:.2f}' if r['sharpe'] is not None else 'N/A'
            out.append(f'| {symbol} | {r["strategy"]} | {final} | {fmt_pct(r["total"]).strip()} | '
                       f'{fmt_pct(r["annual"]).strip()} | {fmt_pct(r["mdd"]).strip()} | {sharpe} | {r["trades"] or 0} |')

    out.append('')
    out.append('## 分年度收益(跨时间稳定性)')
    out.append('')
    out.append('> 注: ma200/tsm_vol 在 2019-2020 有指标预热期; 2026 为 1-9 月不满整年')
    for symbol in SYMBOLS:
        out.append('')
        out.append(f'### {symbol}')
        out.append('')
        out.append('| 策略 | ' + ' | '.join(str(y) for y in years) + ' | 正收益年 | 最差年 |')
        out.append('|---|' + '---|' * (len(years) + 2))
        for r in by_symbol.get(symbol, []):
            yr = yearly_returns(r['curve'])
            cells = ' | '.join(fmt_pct(yr.get(y)).strip() for y in years)
            full_years = [y for y in years if y < CURRENT_YEAR and yr.get(y) is not None]
            pos_n = sum(1 for y in full_years if yr[y] > 0)
            worst_y, worst_v = None, None
            for y in full_years:
                if worst_v is None or yr[y] < worst_v:
                    worst_y, worst_v = y, yr[y]
            worst = f'{worst_y} {fmt_pct(worst_v).strip()}' if worst_y else 'N/A'
            out.append(f'| {r["strategy"]} | {cells} | {pos_n}/{len(full_years)} | {worst} |')
    out.append('')

    text = '\n'.join(out)
    print(text)
    report_dir = os.path.join(ROOT, 'reports')
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, 'crypto_backtest_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(text + '\n')
    print(f'\n报告已写入: {report_path}')


if __name__ == '__main__':
    main()
