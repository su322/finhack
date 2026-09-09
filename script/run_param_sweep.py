# -*- coding: utf-8 -*-
"""参数鲁棒性扫描: tsm30 时间窗口 x donchian 通道参数, 检验策略是否"跨越参数".

用法: python script/run_param_sweep.py [BTCUSDC|ETHUSDC]   (缺省两个都跑)
输出: reports/crypto_param_sweep.md
"""
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

from run_crypto_backtest import (run_one, yearly_returns, fmt_pct,
                                 SYMBOLS, START, END, CASH, CURRENT_YEAR)

# (策略文件名, 额外参数, 展示标签)
SWEEP = [
    ('tsm30',    {'lookback': 10}, 'tsm30_L10'),
    ('tsm30',    {'lookback': 20}, 'tsm30_L20'),
    ('tsm30',    {'lookback': 30}, 'tsm30_L30'),
    ('tsm30',    {'lookback': 60}, 'tsm30_L60'),
    ('tsm30',    {'lookback': 90}, 'tsm30_L90'),
    ('donchian', {'entry_win': 20, 'exit_win': 10}, 'donchian_20x10'),
    ('donchian', {'entry_win': 40, 'exit_win': 20}, 'donchian_40x20'),
    ('donchian', {'entry_win': 55, 'exit_win': 20}, 'donchian_55x20'),
    ('donchian', {'entry_win': 90, 'exit_win': 30}, 'donchian_90x30'),
]
YEARS = list(range(2019, CURRENT_YEAR + 1))


def sweep_symbol(symbol):
    rows = []
    for strategy, extra, label in SWEEP:
        print(f'\n########## RUN {label} @ {symbol} ##########', flush=True)
        rows.append(run_one(strategy, symbol, extra, label))
    return rows


def build_report(symbol, rows):
    out = [f'# 参数鲁棒性扫描 — {symbol}', '']
    out.append(f'- 区间: {START} ~ {END}   初始: {CASH:,.0f} USD   手续费 0.1%/边   滑点 0.05%')
    out.append('- 目的: 检验策略结论是否依赖特定参数(若只有个别参数赚钱则不可信)')
    out.append('')
    out.append('## 全期表现')
    out.append('')
    out.append('| 变体 | 期末资产 | 累计收益 | 年化 | 最大回撤 | 夏普 | 交易次数 |')
    out.append('|---|---|---|---|---|---|---|')
    for r in rows:
        final = f'{r["curve"][-1][1]:,.0f}' if r['curve'] else 'N/A'
        sharpe = f'{r["sharpe"]:.2f}' if r['sharpe'] is not None else 'N/A'
        out.append(f'| {r["strategy"]} | {final} | {fmt_pct(r["total"]).strip()} | '
                   f'{fmt_pct(r["annual"]).strip()} | {fmt_pct(r["mdd"]).strip()} | {sharpe} | {r["trades"] or 0} |')

    out.append('')
    out.append('## 分年度收益')
    out.append('')
    out.append('| 变体 | ' + ' | '.join(str(y) for y in YEARS) + ' | 正收益年 | 最差年 |')
    out.append('|---|' + '---|' * (len(YEARS) + 2))
    for r in rows:
        yr = yearly_returns(r['curve'])
        cells = ' | '.join(fmt_pct(yr.get(y)).strip() for y in YEARS)
        full_years = [y for y in YEARS if y < CURRENT_YEAR and yr.get(y) is not None]
        pos_n = sum(1 for y in full_years if yr[y] > 0)
        worst_y, worst_v = None, None
        for y in full_years:
            if worst_v is None or yr[y] < worst_v:
                worst_y, worst_v = y, yr[y]
        worst = f'{worst_y} {fmt_pct(worst_v).strip()}' if worst_y else 'N/A'
        out.append(f'| {r["strategy"]} | {cells} | {pos_n}/{len(full_years)} | {worst} |')

    out.append('')
    out.append('## 鲁棒性小结')
    out.append('')
    for family in ('tsm30', 'donchian'):
        grp = [r for r in rows if r['strategy'].startswith(family)]
        totals = [r['total'] for r in grp if r['total'] is not None]
        worst_years = []
        for r in grp:
            yr = yearly_returns(r['curve'])
            full = [yr[y] for y in YEARS if y < CURRENT_YEAR and yr.get(y) is not None]
            if full:
                worst_years.append(min(full))
        n_pos = sum(1 for t in totals if t > 0)
        out.append(f'- **{family}**: {n_pos}/{len(totals)} 个参数变体全期正收益; '
                   f'最差变体累计 {fmt_pct(min(totals)).strip()}, 最好变体 {fmt_pct(max(totals)).strip()}; '
                   f'各变体最差年度区间 {fmt_pct(min(worst_years)).strip()} ~ {fmt_pct(max(worst_years)).strip()}')
    out.append('')
    return '\n'.join(out)


def main():
    symbols = sys.argv[1:] or SYMBOLS
    for symbol in symbols:
        rows = sweep_symbol(symbol)
        text = build_report(symbol, rows)
        print(text)
        path = os.path.join(ROOT, 'reports', f'crypto_param_sweep_{symbol}.md')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text + '\n')
        print(f'\n报告已写入: {path}')


if __name__ == '__main__':
    main()
