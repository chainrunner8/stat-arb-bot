
import asyncio
import warnings
import numpy as np
from configExecution import config
from wsConnection import ws
from tradeManager import TradeManager
from statAnalysis import get_latest_z_score

warnings.simplefilter(action='ignore', category=FutureWarning)


tradeManager = TradeManager()

# place_market_order(TICKER_1, "buy", 1)
# place_limit_order("post", TICKER_1, "sell", 1, 142.3)
# close_all_positions_and_orders()

# get_position_info(TICKER_1)

# close_all_positions_and_orders()

# response = exec_config.set_leverage(TICKER_1)
# print(response.json())


''' maybe not the most elegant way to go about it but it works: '''

trading = False
trigger_z_sign = 0
quantity_1 = 0
quantity_2 = 0


async def trade():

    global trading
    global quantity_1
    global quantity_2
    global trigger_z_sign

    # check if z_score is good:
    z_score = get_latest_z_score()
    print(f"Latest Z-score: {z_score}")

    if z_score is None:
        print('!!! Could not compute Z-score due to incomplete price data. Try trading another pair. Exiting... !!!')
        raise Exception

    # if not trading AND z-score is beyond trigger threshold, then init order execution and set trading to True
    if not trading and abs(z_score) >= config.trigger_threshold:
        trading = True
        trigger_z_sign = np.sign(z_score)

        if np.sign(z_score) == 1:  # spread is positive
            quantity_1 = tradeManager.init_order_exec(config.ticker_1, 'sell')[2]
            quantity_2 = tradeManager.init_order_exec(config.ticker_2, 'buy')[2]
        else:  # spread is negative
            quantity_1 = tradeManager.init_order_exec(config.ticker_1, 'buy')[2]
            quantity_2 = tradeManager.init_order_exec(config.ticker_2, 'sell')[2]

    # if limit orders were placed but not all filled yet and Z-score dumps far below threshold, cancel entire trade
    elif trading \
            and z_score < config.trigger_threshold * (1 - config.LO_delta) \
            and not tradeManager.all_orders_filled(quantity_1, quantity_2):
        await tradeManager.close_all_positions_and_orders()
        trading = False

    # if trading AND (z-score has crossed 0 or z-score is 0), then exit positions and set trading to False
    elif trading and (np.sign(z_score) == -np.sign(trigger_z_sign) or z_score == 0):
        await tradeManager.close_all_positions_and_orders()
        trading = False


async def run_bot():

    print('Henlo, Statbot wif hat inithiating...')

    # subscribe to live price feed for both tickers:
    ws.subscribe_feed([config.ticker_1, config.ticker_2])

    # run bot:
    print('Theeking tradeth...')
    while True:
        await asyncio.gather(asyncio.sleep(10), trade())


if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(tradeManager.close_all_positions_and_orders())
        print('Bot wif hat going to thleep.')
        loop.close()
