
import json
import numpy as np
from configExecution import config
from wsConnection import ws_conn


""" config params used in this module: ticker_1, stop_loss, capital"""


# get price rounding and quantity rounding params:
def get_ticker_params(ticker):

    with open("../../Data/instruments.json") as file:
        data = json.load(file)
    instruments = data['result']['list']

    ticker_params = next(
        inst
        for inst in instruments
        if inst['symbol'] == ticker
    )

    tick_size = float(ticker_params['priceFilter']['tickSize'])
    # if tick size is half a decimal (e.g. 0.05), round to nearest half, else to the nearest decimal:
    if str(tick_size)[-1] == '5':
        price_rounding = {
            'rounding': 5,
            'decimals': int("{:.0e}".format(tick_size)[-1]) - 1
        }
    else:
        price_rounding = {
            'rounding': 1,
            'decimals': -round((np.log(tick_size) / np.log(10)))
        }

    qty_step = float(ticker_params['lotSizeFilter']['qtyStep'])
    # if quantity step is half a power of ten (e.g. 5), round to nearest half, else to the nearest decimal:
    if str(qty_step)[-1] == '5':
        qty_rounding = {
            'rounding': 5,
            'decimals': int("{:.0e}".format(qty_step)[-1]) - 1
        }
    else:
        qty_rounding = {
            'rounding': 1,
            'decimals': -round((np.log(qty_step) / np.log(10)))
        }

    return price_rounding, qty_rounding


# get trade details and latest prices
def get_trade_params(capital, ticker, side, price_rounding, qty_rounding):

    if ticker == config.ticker_1:
        bid_ask = ws_conn.ticker_1_bid_ask
    else:
        bid_ask = ws_conn.ticker_2_bid_ask

    # placing at bid/ask has higher probability of not being cancelled, but may not easily fill:
    if side == "Buy":
        mid_price = bid_ask[0]  # bid_ask[0] = bid
    else:
        mid_price = bid_ask[1]  # bid_ask[1] = ask

    # round stop loss price:
    stop_loss = 1 - config.stop_loss if side == 'Buy' else 1 + config.stop_loss
    stp = mid_price * stop_loss
    p_decimals = price_rounding['decimals']

    if price_rounding['rounding'] == 5:
        stop_price = round(2*10**p_decimals * stp) / (2*10**p_decimals)  # formula to round to the nearest half
    else:
        stop_price = round(stp, p_decimals)

    # round order quantity:
    qty = capital / mid_price  # we give the bot equal amounts of capital to trade on ticker 1 and 2
    q_decimals = qty_rounding['decimals']

    if qty_rounding['rounding'] == 5:
        quantity = round(2*10**q_decimals * qty) / (2*10**q_decimals)  # formula to round to the nearest half
    else:
        quantity = round(qty, q_decimals)

    return mid_price, stop_price, quantity
