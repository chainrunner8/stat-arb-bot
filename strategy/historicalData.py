
import requests
import json
import datetime as dt
import time
from configStrategy import config


def get_tradeable_symbols():

    with open("../../Data/instruments.json") as file:  # all existing instruments that can be traded on Kraken Futures and their details.
        data = json.load(file)

    symbols = []
    for inst in data['instruments']:
        if inst['tradeable']:
            symbol = inst['symbol']
            if symbol[:2] == 'PF' and not ('USDC' in symbol or 'USDT' in symbol):  # we only want to trade PF (linear perpetuals) that are currently tradeable excluding USDT/C.
                symbols.append(symbol)
                
    return symbols


def get_historical_prices():
    hist_data = {}
    symbols = get_tradeable_symbols()
    today = dt.datetime.now() - dt.timedelta(hours=config.lookback)
    params = {'from': int(today.timestamp())}
    counter = 0

    for symbol in symbols:
        time.sleep(0.1)

        try:
            response = requests.get(f"https://futures.kraken.com/api/charts/v1/spot/{symbol}/{config.timeframe}", params=params)
        except Exception as e:
            print(f'Failed to fetch historical data for {symbol}:', e)
            continue
        candles = response.json()
        symbol_data = [float(candle['close']) for candle in candles['candles']]
        if len(symbol_data) == config.lookback:
            hist_data[symbol] = symbol_data
            counter += 1
            print(f"{counter} symbols data fetched.")
        else:
            continue

    with open("../../Data/historical_prices.json", 'w') as file:
        json.dump(hist_data, file, indent=4)
        print('Prices saved.')



