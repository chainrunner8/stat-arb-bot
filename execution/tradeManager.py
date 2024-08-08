
import time
from configExecution import config
from tradeConfig import get_ticker_params, get_trade_params
from pybit.unified_trading import HTTP


''' constants '''
MAX_RETRIES = 15


class TradeManager:

    def __init__(self):
        # objects:
        self.private_session = HTTP(demo=True, api_key=config.api_public, api_secret=config.api_secret)

        # ticker params:
        self.rounding = {}

        # order variables:
        self.order_ids = {}
        self.order_statuses = {}

        # init functions:
        self._set_rounding()

    def _set_rounding(self):

        self.rounding[config.ticker_1] = dict(zip(['price rnd', 'qty rnd'], get_ticker_params(config.ticker_1)))
        self.rounding[config.ticker_2] = dict(zip(['price rnd', 'qty rnd'], get_ticker_params(config.ticker_2)))

    def get_position_info(self):

        try:
            response = self.private_session.get_positions(category='linear', settleCoin='USDT')
        except Exception as e:
            print(f"!!! Failed to fetch open positions !!!", e)
        else:
            return response['result']['list']

    def get_current_pnl(self):

        positions = self.get_position_info()
        pnl = 0
        for pos in positions:
            pnl += float(pos['curRealisedPnl']) + float(pos['unrealisedPnl'])
        return round(pnl, 2)

    def place_market_order(self, ticker, side, size):

        retries = 0

        while retries <= MAX_RETRIES:
            try:
                # send market order:
                response = self.private_session.place_order(
                    category='linear',
                    symbol=ticker,
                    side=side,
                    orderType='Market',
                    qty=str(size)
                )
            except Exception as e:
                print(f"!!! Failed to send market-{side} order for {ticker} !!!", e)
                retries += 1
            else:
                # get order id and then get order details:
                order_id = response['result']['orderId']
                response = self.private_session.get_open_orders(category='linear', orderId=order_id)
                order_details = response['result']['list'][0]
                status = order_details['orderStatus']

                # retry if order status = cancelled:
                if status == 'Cancelled' or status == 'Rejected':
                    retries += 1
                    if retries <= MAX_RETRIES:
                        print(f"Market-{side} order for {ticker} cancelled. Retrying {retries} time(s)...")
                    continue
                else:
                    print(f"Market-{side} order for {ticker} successfully placed at "
                          f"${order_details['avgPrice']}.")
                    return

        # max retries exceeded:
        print(f"!!! Market-{side} order for {ticker} could not be placed after {MAX_RETRIES} retries !!!")

    # place post-only limit order
    def place_limit_order(self, capital, ticker, side, stop_price=''):

        price_rounding = self.rounding[ticker]['price rnd']
        qty_rounding = self.rounding[ticker]['qty rnd']
        retries = 0

        while retries <= MAX_RETRIES:

            start_time = time.time()
            price, _, size = get_trade_params(capital, ticker, side, price_rounding,
                                              qty_rounding)  # replace _ with stop_price

            try:
                # send limit order:
                response = self.private_session.place_order(
                    category='linear',
                    symbol=ticker,
                    side=side,
                    orderType='Limit',
                    qty=str(size),
                    price=str(price),
                    timeInForce='PostOnly',
                    stopLoss=str(stop_price)
                )
                end_time = time.time()
                print(f"Execution time: {round(end_time - start_time, 2)}s")
            except Exception as e:
                print(f"!!! Failed to send limit-{side} order for {ticker} !!!", e)
                retries += 1
            else:
                # get order id, then get order details:
                order_id = response['result']['orderId']
                response = self.private_session.get_open_orders(category='linear', orderId=order_id)
                order_details = response['result']['list'][0]
                status = order_details['orderStatus']

                # if order status = cancelled, get latest orderbook info, recompose the order and retry:
                if status == 'Cancelled' or status == 'Rejected':
                    retries += 1
                    if retries <= MAX_RETRIES:
                        print(f"Limit-{side} order for {ticker} cancelled. Retrying {retries} time(s)...")
                    print(f"Price: ${price}")
                    continue
                else:
                    print(f"Limit-{side} order for {ticker} successfully placed at "
                          f"${order_details['price']}.")
                    self.order_ids[ticker] = order_id  # log the order id if successfully placed
                    return 0

        # max retries exceeded:
        print(f"!!! Limit-{side} order for {ticker} could not be placed after {MAX_RETRIES} retries !!!")
        return -1

    # upon getting a Z-score signal to open a position on a pair:
    def init_order_exec(self, ticker_1_side, ticker_2_side):

        # first set leverage for the ticker:
        # self.private_session.set_leverage(
        #     category='linear',
        #     symbol=ticker,
        #     buyLeverage="1",
        #     sellLeverage="1"
        # )
        capital = config.capital / 2
        ks_1 = self.place_limit_order(capital, config.ticker_1, ticker_1_side)  # add stp_price if SL.
        ks_2 = self.place_limit_order(capital, config.ticker_2, ticker_2_side)  # add stp_price if SL.

        # if an order couldn't be placed after max retries, cancel entire trade:
        if ks_1 + ks_2 != 0:
            self.close_all_positions_and_orders()
            return -1
        return 0

    # upon getting a Z-score signal to close existing positions on the pair:
    def close_all_positions_and_orders(self):

        # cancel all active orders:
        try:
            response = self.private_session.cancel_all_orders(category='linear', settleCoin="USDT")
        except Exception as e:
            print("!!! Failed to cancel all open orders !!!", e)
        else:
            if response['result']['success'] == '1':
                print("All orders successfully cancelled.")
            else:
                print("!!! Failed to cancel all open orders !!!", response)

        # close all open positions:
        positions = self.get_position_info()
        pos_1 = next(
            pos
            for pos in positions
            if pos['symbol'] == config.ticker_1
        )
        pos_2 = next(
            pos
            for pos in positions
            if pos['symbol'] == config.ticker_2
        )
        side_1, size_1 = pos_1['side'], pos_1['size']  # coulda saved that in class attribute, but too lazy to code
        side_2, size_2 = pos_2['side'], pos_2['size']

        if float(size_1) > 0:  # only market close a position that's been at least partially filled.
            if side_1 == 'Buy':
                self.place_market_order(config.ticker_1, 'Sell', size_1)
            else:
                self.place_market_order(config.ticker_1, 'Buy', size_1)
            print(f"{config.ticker_1} position successfully closed.")

        if float(size_2) > 0:
            if side_2 == 'Buy':
                self.place_market_order(config.ticker_2, 'Sell', size_2)
            else:
                self.place_market_order(config.ticker_2, 'Buy', size_2)
            print(f"{config.ticker_2} position successfully closed.")

        # reset order log:
        self.order_ids = {}
        self.order_statuses = {}

    def all_orders_filled(self):

        order_ticker_1 = self.private_session.get_open_orders(
            category='linear',
            orderId=self.order_ids[config.ticker_1]
        )['result']['list'][0]
        self.order_statuses[config.ticker_1] = order_ticker_1
        status_ticker_1 = order_ticker_1['orderStatus']

        order_ticker_2 = self.private_session.get_open_orders(
            category='linear',
            orderId=self.order_ids[config.ticker_2]
        )['result']['list'][0]
        self.order_statuses[config.ticker_2] = order_ticker_2
        status_ticker_2 = order_ticker_2['orderStatus']

        if status_ticker_1 == 'Filled' and status_ticker_2 == 'Filled':  # check if both orders are fully filled
            return True
        return False

    def move_limit_orders(self):

        ks_1, ks_2 = 0, 0
        # get leavesValue (remaining unfilled capital) for both orders.
        leaves_ticker_1 = float(self.order_statuses[config.ticker_1]['leavesValue'])
        leaves_ticker_2 = float(self.order_statuses[config.ticker_2]['leavesValue'])

        side_ticker_1 = self.order_statuses[config.ticker_1]['side']
        side_ticker_2 = self.order_statuses[config.ticker_2]['side']

        # move LOs if there's any remaining unfilled capital:
        if leaves_ticker_1 > 0:
            self.private_session.cancel_order(
                category='linear',
                symbol=config.ticker_1,
                orderId=self.order_ids[config.ticker_1]
            )
            ks_1 = self.place_limit_order(leaves_ticker_1, config.ticker_1, side_ticker_1)
        if leaves_ticker_2 > 0:
            self.private_session.cancel_order(
                category='linear',
                symbol=config.ticker_2,
                orderId=self.order_ids[config.ticker_2]
            )
            ks_2 = self.place_limit_order(leaves_ticker_2, config.ticker_2, side_ticker_2)

        # if an order couldn't be placed after max retries, cancel entire trade:
        if ks_1 + ks_2 != 0:
            self.close_all_positions_and_orders()
            return -1
        return 0
