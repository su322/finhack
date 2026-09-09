# -*- coding: utf-8 -*-
"""双均线(单币种): 收盘价 SMA20 上穿 SMA60 全仓买入, 下穿清仓.

运行参数: params='{"symbol": "BTCUSDC"}' 或 "ETHUSDC", 默认 BTCUSDC.
"""


def initialize(context):
    g.symbol = context.get('params', {}).get('symbol', 'BTCUSDC')
    set_benchmark(g.symbol)
    set_order_cost(OrderCost(open_tax=0, close_tax=0,
                             open_commission=0.001, close_commission=0.001,
                             min_commission=0), type='crypto')
    set_slippage(0.0005, type='crypto')
    g.short_win = 20
    g.long_win = 60
    g.closes = []
    run_daily(trade, time="23:55:00")


def _sma(values, win):
    if len(values) < win:
        return None
    return sum(values[-win:]) / win


def trade(context):
    price = get_current_price(context, g.symbol)
    if not price:
        return
    g.closes.append(price)

    sma_s = _sma(g.closes, g.short_win)
    sma_l = _sma(g.closes, g.long_win)
    if sma_s is None or sma_l is None:
        return

    pos = get_positions(symbol=g.symbol)
    volume = sum(p.volume for p in pos)

    if sma_s > sma_l and volume <= 0:
        cash = get_cash()
        volume = int(cash * 0.98 / price * 10000) / 10000
        if volume >= 0.0001 and volume * price <= cash:
            order_buy(context, g.symbol, volume)
    elif sma_s < sma_l and volume > 0:
        order_sell(context, g.symbol, volume)
