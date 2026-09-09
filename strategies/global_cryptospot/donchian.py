# -*- coding: utf-8 -*-
"""唐奇安通道突破(海龟, 单币种): 收盘价创 entry_win 日新高全仓买入,
跌破 exit_win 日最低清仓. 经典趋势跟踪.


运行参数: params='{"symbol": "BTCUSDC", "entry_win": 55, "exit_win": 20}',
默认 55/20.
"""


def initialize(context):
    g.symbol = context.get('params', {}).get('symbol', 'BTCUSDC')
    g.entry_win = int(context.get('params', {}).get('entry_win', 55))
    g.exit_win = int(context.get('params', {}).get('exit_win', 20))
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

    pos = get_positions(symbol=g.symbol)
    volume = sum(p.volume for p in pos)

    if volume <= 0:
        if len(g.closes) >= g.entry_win + 1:
            prior_high = max(g.closes[-(g.entry_win + 1):-1])
            if price > prior_high:
                cash = get_cash()
                volume = int(cash * 0.98 / price * 10000) / 10000
                if volume >= 0.0001 and volume * price <= cash:
                    order_buy(context, g.symbol, volume)
    else:
        if len(g.closes) >= g.exit_win + 1:
            prior_low = min(g.closes[-(g.exit_win + 1):-1])
            if price < prior_low:
                order_sell(context, g.symbol, volume)
