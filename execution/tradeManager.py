
from configExecution import config
from sessionPrivate import SessionPrivate
from tradeConfig import get_trade_params


MAX_RETRIES = 5

# position filled: buy more
# order active: do nothing
# order partially filled: do nothing
# order cancelled: place again
# if order hasn't filled on both sides in x minutes: move order or cancel eet? --> check Z-score


class TradeManager(SessionPrivate):

    def __init__(self):
        super().__init__()

    def get_position_info(self, ticker):

        try:
            response = self.get_open_positions()
        except Exception as e:
            print(f"!!! Failed to fetch open positions for {ticker} !!!", e)
        else:
            data = response.json()
            if data['result'] == 'success':
                # find positions on specified symbol:
                try:
                    position = next(
                        pos for pos in data['openPositions']
                        if pos['symbol'] == ticker
                    )
                except StopIteration:
                    return None, 0
                else:
                    side = "buy" if position['side'] == "long" else "sell"
                    size = position['size']
                    return side, size
            else:
                print(f"!!! Failed to fetch open positions for {ticker} !!!", data)

    def place_market_order(self, ticker, side, size):

        # populate request body
        order = {
            'orderType': 'mkt',
            'side': side,
            'size': size,
            'symbol': ticker
        }

        placed = False
        retries = 0

        while not placed and retries < MAX_RETRIES:

            try:
                # send market order
                response = self.send_order(order)
            except Exception as e:
                print(f"!!! Failed to send market-{side} order for {ticker} !!!", e)
                return
            else:
                order_details = response.json()

                if order_details['result'] == 'success':

                    status = order_details['sendStatus']['status']
                    if status == 'placed':  # check if order was placed or cancelled
                        print(f"Market-{side} order for {ticker} successfully placed at "
                              f"${order_details['sendStatus']['orderEvents'][0]['price']}.")
                        return
                    elif status == 'cancelled' or status == 'iocWouldNotExecute':  # retry if cancelled
                        print(f"Market-{side} order for {ticker} cancelled. Retrying...")
                        retries += 1
                    else:
                        print(f"!!! Failed to send market-{side} order for {ticker} !!!", order_details)
                        return
                else:
                    print(f"An error occurred while sending a market order for {ticker}.")
                    print("!!! Output message:", order_details)
                    return

        # max retries exceeded:
        print(f"!!! Market-{side} order for {ticker} could not be placed after {MAX_RETRIES} retries !!!")

    # place post-only limit order
    def place_limit_order(self, order_type, ticker, side, size, price):

        # type is one of: 'post' or 'stp'
        # populate request body:
        if order_type == 'post':
            order = {
                'orderType': order_type,
                'side': side,
                'size': size,
                'symbol': ticker,
                'limitPrice': price,
                'reduceOnly': False
            }
        else:  # stop order:
            order = {
                'orderType': order_type,
                'side': side,
                'size': size,
                'symbol': ticker,
                'reduceOnly': True,
                'stopPrice': price
            }

        placed = False
        retries = 0

        while not placed and retries < MAX_RETRIES:

            try:
                # send limit order
                response = self.send_order(order)
            except Exception as e:
                print(f"!!! Failed to send limit-{side} order for {ticker} !!!", e)
            else:
                order_details = response.json()

                if order_details['result'] == 'success':  # check if order was placed or cancelled

                    status = order_details['sendStatus']['status']
                    if status == 'placed':
                        if order_type == 'post':
                            print(f"Limit-{side} order for {ticker} successfully placed at "
                                  f"${order_details['sendStatus']['orderEvents'][0]['order']['limitPrice']}.")
                        else:
                            print(f"Stop-{side} order for {ticker} successfully placed at "
                                  f"${order_details['sendStatus']['orderEvents'][0]['orderTrigger']['triggerPrice']}.")
                        print(order_details)
                        return

                    # TODO: if Z-score falls below config.LO_delta, cancel all orders and market-close positions. DONE.

                    elif status == 'cancelled' or status == 'postWouldExecute':  # retry if cancelled
                        print(f"Limit-{side} order for {ticker} cancelled. Retrying...")
                        retries += 1
                    else:
                        print(f"!!! Failed to send limit-{side} order for {ticker} !!!", order_details)
                        return
                else:
                    print(f"An error occurred while sending a limit order for {ticker}")
                    print("!!! Output message:", order_details)
                    return

    # upon getting a Z-score signal to open a position on the pair:
    def init_order_exec(self, ticker, side):

        # first set leverage for both markets:
        self.set_leverage(config.ticker_1)
        self.set_leverage(config.ticker_2)

        # then get trade details:
        entry_price, stop_loss_price, quantity = get_trade_params(ticker, side)
        stop_side = 'sell' if side == 'buy' else 'buy'

        # send limit order to open position, and set stop order:
        self.place_limit_order('post', ticker, side, quantity, entry_price)
        self.place_limit_order('stp', ticker, stop_side, quantity, stop_loss_price)

        return entry_price, stop_loss_price, quantity

    # upon getting a Z-score signal to close existing positions on the pair:
    async def close_all_positions_and_orders(self, killswitch=1):

        # cancel all active orders
        try:
            response = self.cancel_all_orders()
        except Exception as e:
            print("!!! Failed to cancel all open orders !!!", e)
        else:
            data = response.json()
            if data['result'] == 'success':
                print("All orders successfully cancelled.")
            else:
                print("!!! Failed to cancel all open orders !!!", data)

        # close all open positions
        side_1, size_1 = self.get_position_info(config.ticker_1)
        side_2, size_2 = self.get_position_info(config.ticker_2)

        if size_1 > 0:  # only market close a position that's been at least partially filled.
            if side_1 == 'buy':
                self.place_market_order(config.ticker_1, 'sell', size_1)
            else:
                self.place_market_order(config.ticker_1, 'buy', size_1)
            print(f"{config.ticker_1} position successfully closed.")

        if size_2 > 0:
            if side_2 == 'buy':
                self.place_market_order(config.ticker_2, 'sell', size_2)
            else:
                self.place_market_order(config.ticker_2, 'buy', size_2)
            print(f"{config.ticker_2} position successfully closed.")

        killswitch = 0  # literally useless, idk why this is here

        return killswitch

    def check_fill_status(self, ticker, quantity):

        ticker_fill = self.get_position_info(ticker)[1]  # gets position size

        if ticker_fill < quantity:  # not filled if position size < ordered quantity
            return False
        else:
            return True

    def all_orders_filled(self, qty_1, qty_2):

        if not self.check_fill_status(config.ticker_1, qty_1) or not self.check_fill_status(config.ticker_2, qty_2):
            return False
        else:
            return True
