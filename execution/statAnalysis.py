
import requests
import datetime as dt
import statistics as stat
import pandas as pd
from configExecution import config
from wsConnection import ws


def get_lookback_prices(ticker):

    # define period over which we fetch close prices (lookback)
    if 'h' in config.timeframe:
        multiplier = int(config.timeframe.split('h')[0])
        from_ = dt.datetime.now() - dt.timedelta(hours=(config.z_score_window - 1) * multiplier)
    else:
        multiplier = int(config.timeframe.split('m')[0])
        from_ = dt.datetime.now() - dt.timedelta(minutes=(config.z_score_window - 1) * multiplier)

    params = {
        'from': int(from_.timestamp()),
        # 'to': int(to.timestamp())
    }
    # send out request
    try:
        response = requests.get(
            url=f"https://futures.kraken.com/api/charts/v1/{config.tick_type}/{ticker}/{config.timeframe}",
            params=params
        )
    except Exception as e:
        print(f'Failed to fetch historical data for {ticker}:', e)
    else:
        data = response.json()
        close_prices = [float(candle['close']) for candle in data['candles']]

        if len(close_prices) == config.z_score_window - 1:
            # return
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
        # add the latest price to the lookback prices list for both tickers:
        ticker_1_prices.append(ws.ticker_1_mid_price)
        ticker_2_prices.append(ws.ticker_2_mid_price)

        # spread:
        spread = list(pd.Series(ticker_1_prices) - pd.Series(ticker_2_prices) * config.hedge_ratio)

        # z-score:
        z_score = (spread[-1] - stat.mean(spread)) / stat.stdev(spread)

        return z_score
