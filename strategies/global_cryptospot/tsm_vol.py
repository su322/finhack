# -*- coding: utf-8 -*-
"""动量+波动率目标(单币种): 90 日动量为正才有持仓资格,
仓位 = min(1, 目标波动率/30日已实现年化波动率), 每日再平衡.
高波动自动减仓、熊市空仓, 目标是全时段稳健(压回撤、稳夏普).


运行参数: params='{"symbol": "BTCUSDC"}', 默认 BTCUSDC.
"""
import math


def initialize(context):
    g.symbol = context.get('params', {}).get('symbol', 'BTCUSDC')
    set_benchmark(g.symbol)
    set_order_cost(OrderCost(open_tax=0, close_tax=0,
                             open_commission=0.001, close_commission=0.001,
                             min_commission=0), type='crypto')
    set_slippage(0.0005, type='crypto')
    g.lookback = 90        # 动量观察期
    g.vol_win = 30         # 已实现波动窗口
    g.target_vol = 0.60    # 目标年化波动率
    g.closes = []
    run_daily(trade, time="23:55:00")


def _realized_vol(closes, win):
    rets = [closes[-i] / closes[-i - 1] - 1 for i in range(1, win + 1)]
    mean = sum(rets) / win
    var = sum((r - mean) ** 2 for r in rets) / (win - 1)
    return math.sqrt(var) * math.sqrt(365)


def trade(context):
    price = get_current_price(context, g.symbol)
    if not price:
        return
    g.closes.append(price)
    if len(g.closes) < g.lookback + g.vol_win + 1:
        return

    mom = price / g.closes[-(g.lookback + 1)] - 1
    rv = _realized_vol(g.closes, g.vol_win)

    frac = 0.0 if mom < 0 or rv <= 0 else min(1.0, g.target_vol / rv)

    pos = get_positions(symbol=g.symbol)
    volume = sum(p.volume for p in pos)
    equity = get_account().total_assets
    target_value = equity * frac
    cur_value = volume * price
    delta = target_value - cur_value

    if delta > equity * 0.01:
        cash = get_cash()
        amount = min(delta, cash * 0.98)
        vol = int(amount / price * 10000) / 10000
        if vol >= 0.0001 and vol * price <= cash:
            order_buy(context, g.symbol, vol)
    elif delta < -equity * 0.01 and volume > 0:
        vol = int(min(-delta / price, volume) * 10000) / 10000
        if vol >= 0.0001:
            order_sell(context, g.symbol, vol)
