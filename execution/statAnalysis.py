
""" Possible timeframe values: 1,3,5,15,30,60,120,240,360,720,D """


import datetime as dt
import statistics as stat
import pandas as pd
from configExecution import config
from pybit.unified_trading import HTTP

""" config params used in this module: timeframe, z_score_window, ticker_1 & 2, hedge_ratio """

# session object to call the methods that'll return our data.
session = HTTP()


def get_lookback_prices(ticker):

    # define period over which we fetch close prices (lookback)
    if config.timeframe == 'D':
        start = dt.datetime.now() - dt.timedelta(days=config.z_score_window)
    else:
        start = dt.datetime.now() - dt.timedelta(minutes=config.z_score_window * int(config.timeframe))

    start_ts = round(start.timestamp() * 1000)  # Bybit wants timestamps in milliseconds

    # send out request
    try:
        response = session.get_kline(
            symbol=ticker,
            interval=config.timeframe,
            start=start_ts
        )
    except Exception as e:
        print(f'Failed to fetch historical data for {ticker}:', e)
    else:
        klines = response.get('result', {}).get('list', [])
        close_prices = [float(candle[4]) for candle in klines]
        close_prices = close_prices[::-1]

        if len(close_prices) == config.z_score_window:
            return close_prices
        else:
            print('!!! Incomplete lookback price data for Z-score calculation !!!')
            print(close_prices)
            # choose a different pair to trade
            return None


def get_latest_z_score():

    # get lookback prices list for both tickers
    ticker_1_prices = get_lookback_prices(config.ticker_1)
    ticker_2_prices = get_lookback_prices(config.ticker_2)

    # breaking out of the bot's trading loop if Z-score can't be computed, bc strategy can't be carried out properly:
    if ticker_1_prices is None or ticker_2_prices is None:
        return None
    else:
        spread = list(
            pd.Series(ticker_1_prices) -
            (pd.Series([config.const] * config.z_score_window) + pd.Series(ticker_2_prices) * config.hedge_ratio)
        )
        z_score = (spread[-1] - stat.mean(spread)) / stat.stdev(spread)
        return z_score
