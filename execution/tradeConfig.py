
import json
import numpy as np
from configExecution import config
from wsConnection import ws


# get price rounding and quantity rounding params:
def get_ticker_params(ticker):

    with open("../../Data/instruments.json") as file:
        data = json.load(file)

    ticker_params = next(
        inst
        for inst in data['instruments']
        if inst['symbol'] == ticker
    )

    tick_size = ticker_params['tickSize']
    # half tick sizes (e.g. 0.5) are rounded to the decimal above:
    price_rounding = round(abs(np.log(tick_size) / np.log(10)))

    qty_rounding = ticker_params['contractValueTradePrecision']

    return price_rounding, qty_rounding


# get trade details and latest prices
def get_trade_params(ticker, side):

    price_rounding, qty_rounding = get_ticker_params(ticker)

    if ticker == config.ticker_1:
        bid_ask = ws.ticker_1_bid_ask
    else:
        bid_ask = ws.ticker_2_bid_ask

    # get the latest price, SL and qty
        # placing at bid/ask has higher probability of not being cancelled, but may not fill
    if side == "buy":
        mid_price = bid_ask[0]  # bid_ask[0] = bid
    else:
        mid_price = bid_ask[1]  # bid_ask[1] = ask

    stop_loss = 1 - config.stop_loss if side == 'buy' else 1 + config.stop_loss
    stop_price = round(mid_price * stop_loss, price_rounding)

    quantity = round(config.capital / mid_price, qty_rounding)

    return mid_price, stop_price, quantity
