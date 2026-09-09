# -*- coding: utf-8 -*-
"""时间序列动量 TSM(单币种): lookback 日收益 > 0 全仓持有, 否则空仓.
学术上被反复验证跨资产稳健的时间序列动量规则.


运行参数: params='{"symbol": "BTCUSDC", "lookback": 30}', lookback 默认 30.
"""


def initialize(context):
    g.symbol = context.get('params', {}).get('symbol', 'BTCUSDC')
    g.lookback = int(context.get('params', {}).get('lookback', 30))
    set_benchmark(g.symbol)
    set_order_cost(OrderCost(open_tax=0, close_tax=0,
                             open_commission=0.001, close_commission=0.001,
                             min_commission=0), type='crypto')
    set_slippage(0.0005, type='crypto')
    g.closes = []
    run_daily(trade, time="23:55:00")


def trade(context):
    price = get_current_price(context, g.symbol)
    if not price:
        return
    g.closes.append(price)
    if len(g.closes) < g.lookback + 1:
        return

    mom = price / g.closes[-(g.lookback + 1)] - 1
    pos = get_positions(symbol=g.symbol)
    volume = sum(p.volume for p in pos)

    if mom > 0 and volume <= 0:
        cash = get_cash()
        volume = int(cash * 0.98 / price * 10000) / 10000
        if volume >= 0.0001 and volume * price <= cash:
            order_buy(context, g.symbol, volume)
    elif mom < 0 and volume > 0:
        order_sell(context, g.symbol, volume)
