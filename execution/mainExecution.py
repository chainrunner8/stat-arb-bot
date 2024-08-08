
# libraries
import asyncio
import warnings
import numpy as np
import datetime as dt
from pybit.unified_trading import HTTP
# modules
from configExecution import config
from wsConnection import ws_conn
from tradeManager import TradeManager
from statAnalysis import get_latest_z_score
from tradeLogger import TradeLogger


warnings.simplefilter(action='ignore', category=FutureWarning)


""" maybe not the most elegant way to go about it but it works: """

print('Henlo, Statbot wif hat inithiating...')

''' constants '''
PERIOD_CHECK_FREQ: float = 5  # seconds

''' parameters '''
trading = False
trigger_z_sign = 0
open_time = 0
current_period = None

''' objects '''
session = HTTP(demo=True, api_key=config.api_public, api_secret=config.api_secret)
tradeManager = TradeManager()  # manages all trading activities
tradeLogger = TradeLogger()


''' FUNCTIONS '''


async def is_new_period():

    global current_period

    # get Bybit server time:
    try:
        response = session.get_server_time()
    except Exception as e:
        print("Could not fetch Bybit server time: ", e)
    else:
        timestamp = int(response.get('result').get('timeSecond'))
        time = dt.datetime.fromtimestamp(timestamp)
        print(f"Server time: {time}")
        new_period = False
        # detect if new period according to time frame:
        if config.timeframe == '1':
            if time.second <= PERIOD_CHECK_FREQ:
                new_period = True
        elif config.timeframe in ['5', '15', '30']:
            if time.minute % int(config.timeframe) == 0:
                new_period = True
        elif config.timeframe in ['60', '120', '240', '360', '720']:
            if time.hour % (int(config.timeframe) / 60) == 0:
                new_period = True
        elif config.timeframe == 'D':
            if time.strftime('%H:%M') == '00:00':
                new_period = True

        if new_period:
            current_period = time.replace(second=0, microsecond=0)
            return True
        return False


def trade():

    global trading
    global trigger_z_sign
    global open_time

    kill_switch = 0
    failure = None

    # check if z_score is good:
    z_score = get_latest_z_score()
    print(f"Latest Z-score: {z_score}")

    # log stuff:
    tradeLogger.log_pair_data(current_period, z_score)  # for cointegration analysis
    if trading:
        pnl = tradeManager.get_current_pnl()
        print(pnl)
        tradeLogger.pnl_series.append(pnl)  # save current pnl

    if z_score is None:
        print('!!! Could not compute Z-score due to incomplete price data. Try trading another pair. Exiting... !!!')
        raise Exception

    # if not trading AND z-score is beyond trigger threshold, then init order execution and set trading to True
    if not trading and abs(z_score) >= config.trigger_threshold:
        trading = True
        trigger_z_sign = np.sign(z_score)
        open_time = current_period

        if np.sign(z_score) == 1:  # spread is positive, we short ticker 1 and long ticker 2
            kill_switch = tradeManager.init_order_exec(ticker_1_side='Sell', ticker_2_side='Buy')
        else:  # spread is negative, we long ticker 1 and short ticker 2
            kill_switch = tradeManager.init_order_exec(ticker_1_side='Buy', ticker_2_side='Sell')
        if kill_switch != 0:
            failure = 'cancelled'

    # if the limit orders have not been filled but the signal is still positive, then move the LOs with unused capital
    # to the latest bid/ask:
    elif trading \
            and abs(z_score) >= config.trigger_threshold * (1 - config.LO_delta) \
            and not tradeManager.all_orders_filled():
        # move LOs with unused capital to the latest bid/ask
        kill_switch = tradeManager.move_limit_orders()
        if kill_switch != 0:
            failure = 'cancelled'

    # if the limit orders were placed but not all filled yet and Z-score dumps far below threshold, cancel both trades
    elif trading \
            and abs(z_score) < config.trigger_threshold * (1 - config.LO_delta) \
            and not tradeManager.all_orders_filled():
        kill_switch = -1
        failure = 'unfilled'

    # if trading AND (z-score has crossed 0 or z-score is 0), then exit positions and set trading to False
    elif trading and (np.sign(z_score) == -trigger_z_sign or z_score == 0):
        kill_switch = -1
    else:
        print('nofing to do')

    if kill_switch != 0:
        print('Closing trade...')
        tradeManager.close_all_positions_and_orders()
        tradeLogger.log_trade(session, open_time, current_period, failure)
        tradeLogger.reset_pnl_log()  # clear periodic pnl list
        trading = False


async def run_bot():

    # run bot:
    print('Theeking trades...')

    t_minus_one = False
    while True:
        # check if a new period has started, every x seconds:
        result = await asyncio.gather(is_new_period(), asyncio.sleep(PERIOD_CHECK_FREQ))

        if result[0] and not t_minus_one:  # if new period
            # subscribe to live price feed for both tickers:
            ws_conn.subscribe_feed([config.ticker_1, config.ticker_2])
            # check latest z-score and trade:
            trade()
            # close wss once trading is done:
            ws_conn.unsubscribe_feed([config.ticker_1, config.ticker_2])
        # update t-1 status as we move on to the next iteration:
        t_minus_one = result[0]


async def main():
    bot = asyncio.create_task(run_bot())
    try:
        await bot
    except asyncio.CancelledError:
        pass


''' MAIN LOOP '''


if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    task = loop.create_task(main())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if trading:
            tradeManager.close_all_positions_and_orders()  # close all existing positions & orders
            tradeLogger.log_trade(session, open_time, current_period, failure=None)
        if ws_conn.ws.sock:
            ws_conn.close()  # close wss

        task.cancel()
        loop.run_until_complete(task)
        loop.close()

        tradeLogger.export_log()
        print('Bot wif hat going to thleep.')
