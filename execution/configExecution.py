
""" Timeframe values: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 12h, 1d, 1w """


import os
from dotenv import load_dotenv


load_dotenv()

WSS_DEMO_URL = 'wss://demo-futures.kraken.com/ws/v1'
WSS_LIVE_URL = 'wss://futures.kraken.com/ws/v1'
REST_DEMO_URL = 'https://demo-futures.kraken.com'
REST_LIVE_URL = 'https://futures.kraken.com'

TICKER_1 = "PF_DOGEUSD"
TICKER_2 = "PF_XRPUSD"

ROUNDING_TICKER_1 = 0
ROUNDING_TICKER_2 = 0

CAPITAL = 100
STOP_LOSS = 0.05
TRIGGER_THRESH = 0.1

TIMEFRAME = '15m'
Z_SCORE_WINDOW = 21
HEDGE_RATIO = 0.308


class ExecConfig:

    def __init__(self, ticker_1, ticker_2, timeframe, z_score_window,
                 trigger_threshold, hedge_ratio, capital, stop_loss, tick_type='trade'):
        # API urls
        self.wss_url = WSS_DEMO_URL
        self.rest_url = REST_DEMO_URL
        # api keys:
        self.api_key = str(os.getenv('kraken_demo_futures_public'))
        self.api_secret = str(os.getenv('kraken_demo_futures_private'))
        # pair params:
        self.ticker_1 = ticker_1
        self.ticker_2 = ticker_2
        # trading params:
        self.LO_delta = 0.1
        self.tick_type = tick_type
        # strategy params:
        self.trigger_threshold = trigger_threshold
        self.timeframe = timeframe
        self.z_score_window = z_score_window
        self.hedge_ratio = hedge_ratio  # -----------------------------------------------------------------
        self.capital = capital
        self.stop_loss = stop_loss


config = ExecConfig(TICKER_1, TICKER_2, TIMEFRAME, Z_SCORE_WINDOW, TRIGGER_THRESH, HEDGE_RATIO, CAPITAL, STOP_LOSS)
