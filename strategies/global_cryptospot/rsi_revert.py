# -*- coding: utf-8 -*-
"""RSI 均值回归(单币种): RSI14 < 30 全仓买入, RSI14 > 70 清仓.

运行参数: params='{"symbol": "BTCUSDC"}' 或 "ETHUSDC", 默认 BTCUSDC.
"""


def initialize(context):
    g.symbol = context.get('params', {}).get('symbol', 'BTCUSDC')
    set_benchmark(g.symbol)
    set_order_cost(OrderCost(open_tax=0, close_tax=0,
                             open_commission=0.001, close_commission=0.001,
                             min_commission=0), type='crypto')
    set_slippage(0.0005, type='crypto')
    g.win = 14
    g.closes = []
    run_daily(trade, time="23:55:00")


def _rsi(closes, win):
    if len(closes) < win + 1:
        return None
    gains, losses = [], []
    for i in range(1, win + 1):
        chg = closes[-i] - closes[-i - 1]
        gains.append(max(chg, 0))
        losses.append(max(-chg, 0))
    avg_gain = sum(gains) / win
    avg_loss = sum(losses) / win
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def trade(context):
    price = get_current_price(context, g.symbol)
    if not price:
        return
    g.closes.append(price)

    rsi = _rsi(g.closes, g.win)
    if rsi is None:
        return

    pos = get_positions(symbol=g.symbol)
    volume = sum(p.volume for p in pos)

    if rsi < 30 and volume <= 0:
        cash = get_cash()
        volume = int(cash * 0.98 / price * 10000) / 10000
        if volume >= 0.0001 and volume * price <= cash:
            order_buy(context, g.symbol, volume)
    elif rsi > 70 and volume > 0:
        order_sell(context, g.symbol, volume)
