import json
import pandas as pd
from configExecution import config
from wsConnection import ws_conn

"""
pair_data_df:

index(time)  price_1   price_2   spread   Z-score
period 1
period 2
period 3
.
.
.
"""

"""
trade_df:

index     max drawdown   PnL   duration   failure type
trade 1
trade 2
trade 3
.
.
.
"""

PAIR_COLS = ['price_1', 'price_2', 'spread', 'Z-score']
TRADE_COLS = ['max drawdown', 'PnL', 'duration', 'failure']


class TradeLogger:

    def __init__(self):
        # dataframes:
        self.pair_data_df = pd.DataFrame(columns=PAIR_COLS)
        self.pair_data_df.index.name = 'time'

        self.trade_df = pd.DataFrame(columns=TRADE_COLS)

        # variables:
        self.pnl_series = []
        self.trade_row = 1

    def log_pair_data(self, period, z_score):

        period = period.strftime(config.period_fmt)
        price_1 = ws_conn.ticker_1_mid_price
        price_2 = ws_conn.ticker_2_mid_price
        spread = round(price_1 - (config.const + price_2 * config.hedge_ratio), 2)
        new_row = pd.DataFrame(
            dict(zip(PAIR_COLS, [price_1, price_2, spread, round(z_score, 3)])),
            index=[period]
        )
        self.pair_data_df = pd.concat([self.pair_data_df, new_row])

    def log_trade(self, private_session, open_time, current_period, failure):
        """
        pnl:
        save position opening time
        get closed pnl for the ticker and pass in the open time

        add current r + ur pnl to list every period
        min(list)
        :return:
        """
        open_time = open_time.timestamp()

        # get final (close) trade PnL:
        def get_trade_pnl():
            try:
                response = private_session.get_closed_pnl(
                    category="linear",
                    startTime=round(open_time * 1000)  # time in ms
                )
            except Exception as e:
                print('Could not fetch closed PnL:', e)
            else:
                list_ = response.get('result').get('list')
                pnl = round(sum([float(pos['closedPnl']) for pos in list_]), 2)
                return pnl

        close_pnl = get_trade_pnl()
        # update our trading capital with last trade's PnL:
        config.capital += close_pnl

        # calculate trade duration (nb of trading periods):
        close_time = current_period.timestamp()
        if config.timeframe == 'D':
            duration = int((close_time - open_time) // 86_400)  # 86_400 seconds in 1 day
        else:
            duration = int(2 * ((close_time - open_time) / 60 / int(config.timeframe)) // 2)

        # max drawdown of the trade:
        max_drawdown = min(self.pnl_series)

        # add the new row to the trades dataframe:
        new_row = pd.DataFrame(
            dict(zip(TRADE_COLS, [max_drawdown, close_pnl, duration, failure])),
            index=[self.trade_row]
        )
        self.trade_df = pd.concat([self.trade_df, new_row])
        self.trade_row += 1

    def reset_pnl_log(self):
        self.pnl_series = []

    def export_log(self):
        self.pair_data_df.to_csv(f"../../Data/Live testing/{config.ticker_1}-{config.ticker_2}_pair-data.csv")
        self.trade_df.to_csv(f"../../Data/Live testing/{config.ticker_1}-{config.ticker_2}_trades-data.csv")
