# -*- coding: utf-8 -*-
"""200日均线过滤(单币种): 收盘价在 MA200 上方全仓, 下方清仓.
最经典的加密货币长期趋势规则, 交易极少.


运行参数: params='{"symbol": "BTCUSDC"}', 默认 BTCUSDC.
"""


def initialize(context):
    g.symbol = context.get('params', {}).get('symbol', 'BTCUSDC')
    set_benchmark(g.symbol)
    set_order_cost(OrderCost(open_tax=0, close_tax=0,
                             open_commission=0.001, close_commission=0.001,
                             min_commission=0), type='crypto')
    set_slippage(0.0005, type='crypto')
    g.win = 200
    g.closes = []
    run_daily(trade, time="23:55:00")


def trade(context):
    price = get_current_price(context, g.symbol)
    if not price:
        return
    g.closes.append(price)
    if len(g.closes) < g.win:
        return

    ma = sum(g.closes[-g.win:]) / g.win
    pos = get_positions(symbol=g.symbol)
    volume = sum(p.volume for p in pos)

    if price > ma and volume <= 0:
        cash = get_cash()
        volume = int(cash * 0.98 / price * 10000) / 10000
        if volume >= 0.0001 and volume * price <= cash:
            order_buy(context, g.symbol, volume)
    elif price < ma and volume > 0:
        order_sell(context, g.symbol, volume)
