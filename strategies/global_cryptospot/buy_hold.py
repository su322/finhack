# -*- coding: utf-8 -*-
"""买入持有(单币种): 首日全仓买入 params 指定的币种, 之后不再调仓.

运行参数: params='{"symbol": "BTCUSDC"}' 或 "ETHUSDC", 默认 BTCUSDC.
"""


def initialize(context):
    g.symbol = context.get('params', {}).get('symbol', 'BTCUSDC')
    set_benchmark(g.symbol)
    set_order_cost(OrderCost(open_tax=0, close_tax=0,
                             open_commission=0.001, close_commission=0.001,
                             min_commission=0), type='crypto')
    set_slippage(0.0005, type='crypto')
    g.bought = False
    run_daily(trade, time="23:55:00")


def trade(context):
    if g.bought:
        return
    price = get_current_price(context, g.symbol)
    if not price:
        return
    cash = get_cash()
    volume = int(cash * 0.98 / price * 10000) / 10000
    if volume >= 0.0001 and volume * price <= cash:
        order_buy(context, g.symbol, volume)
        g.bought = True
