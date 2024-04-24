import requests
import json
import datetime as dt
import time


def get_symbols():
    try:
        response = requests.get("https://futures.kraken.com/api/charts/v1/spot")
        symbols = response.json()
        pf_symbols = [x for x in symbols if x[:2] == 'PF']
        return pf_symbols
    except Exception as e:
        print(f'Failed to fetch symbols:', e)


def get_historical_prices(config):
    hist_data = {}
    symbols = get_symbols()
    today = dt.datetime.now() - dt.timedelta(hours=config.lookback)
    params = {'from': int(today.timestamp())}
    counter = 0

    for symbol in symbols:
        time.sleep(0.1)

        try:
            response = requests.get(f"https://futures.kraken.com/api/charts/v1/spot/{symbol}/1h", params=params)
        except Exception as e:
            print(f'Failed to fetch historical data for {symbol}:', e)
            continue
        candles = response.json()
        symbol_data = [float(candle['close']) for candle in candles['candles']]
        if len(symbol_data) == config.lookback and not ('USDC' in symbol or 'USDT' in symbol):
            hist_data[symbol] = symbol_data
            counter += 1
            print(f"{counter} symbols data fetched.")
        else:
            continue

    with open("../../Data/historical_prices.json", 'w') as file:
        json.dump(hist_data, file, indent=4)
        print('Prices saved.')



