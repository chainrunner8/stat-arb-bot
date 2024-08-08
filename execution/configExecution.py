
""" Possible timeframe values: 1,3,5,15,30,60,120,240,360,720,D,M,W """


import os
from dotenv import load_dotenv


load_dotenv()

API_PUBLIC = str(os.getenv('bybit_demo_public'))
API_PRIVATE = str(os.getenv('bybit_demo_private'))

WSS_DEMO_URL = 'wss://stream-demo.bybit.com'
WSS_LIVE_URL = 'wss://futures.kraken.com/ws/v1'
REST_DEMO_URL = 'https://api-demo.bybit.com'
REST_LIVE_URL = 'https://futures.kraken.com'

ticker_1: str = "BTCUSDT"
ticker_2: str = "SOLUSDT"

capital: float = 1000
stop_loss: float = 0.05
trigger_thresh: float = 0.1

timeframe: str = '1'
z_score_window: int = 21
hedge_ratio: float = 402


class ExecConfig:

    def __init__(self, ticker_1, ticker_2, timeframe, z_score_window,
                 trigger_threshold, hedge_ratio, capital, stop_loss):
        # API urls
        self.wss_url = WSS_DEMO_URL
        self.rest_url = REST_DEMO_URL
        # api keys:
        self.api_public = API_PUBLIC
        self.api_secret = API_PRIVATE
        # pair tickers:
        self.ticker_1 = ticker_1
        self.ticker_2 = ticker_2
        # trading params:
        self.LO_delta = 0.1
        # strategy params:
        self.trigger_threshold = trigger_threshold
        self.timeframe = timeframe
        self.z_score_window = z_score_window
        self.hedge_ratio = hedge_ratio  # -----------------------------------------------------------------
        self.const = 0
        self.capital = capital
        self.stop_loss = stop_loss

        if self.timeframe == '1':
            self.period_fmt = '%H:%M'
        elif self.timeframe in ['5', '15', '30']:
            self.period_fmt = '%d-%m %H:%M'
        elif self.timeframe in ['60', '120', '240', '360', '720']:
            self.period_fmt = '%d-%m %H:00'
        elif config.timeframe == 'D':
            self.period_fmt = '%d-%m'


config = ExecConfig(ticker_1, ticker_2, timeframe, z_score_window, trigger_thresh, hedge_ratio, capital, stop_loss)
