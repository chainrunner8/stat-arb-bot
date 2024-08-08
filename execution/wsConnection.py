
""" I had to code my own wss module because you can't unsubscribe from a topic with the WebSocket class of pybit,
which I think is pretty stupid because then I have to break and restart the websocket every time I want to track
the price data of another pair. Someone who's apparently behind pybit said on a GitHub issue that it was on their to-do
list more than 2 years ago, so I guess the list must have been flushed long ago already. """

import json
import statistics as stat
import threading
import logging
import websocket
import sys
import time
from uuid import uuid4
from configExecution import config


WS_USDT_URL = "wss://stream.bybit.com/contract/usdt/public/v3"
LOG_LEVEL = logging.ERROR


class WebSocket:

    def __init__(self):
        self.usdt_url = WS_USDT_URL  # URL for USDT linear contracts

        # wss connection handling:
        self.timeout = 5
        self.ping_interval = 20
        self.custom_ping_msg = json.dumps({"op": "ping"})  # to respond to pong from Bybit server
        self.connecting = False

        # price data attrs:
        self.ticker_1_bid_ask = [0, 0]
        self.ticker_2_bid_ask = [0, 0]
        self.ticker_1_mid_price = 0
        self.ticker_2_mid_price = 0

        # configure logging:
        self.logger = None
        self.config_logger()

        self._connect()

    def _connect(self):

        self.connecting = True

        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            url=self.usdt_url,
            on_open=lambda ws, *args: self._on_open(),
            on_message=lambda ws, message: self._on_message(message),
            on_error=lambda ws, error: self._on_error(error),
            on_close=lambda ws, *args: self._on_close(),
            on_pong=lambda ws, *args: self._on_pong()
        )
        self.ws_thread = threading.Thread(target=lambda: self.ws.run_forever(ping_interval=20))
        self.ws_thread.start()

        conn_timeout = self.timeout
        while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout:
            time.sleep(1)
            conn_timeout -= 1

        if not conn_timeout:
            self.logger.info("Couldn't connect to", self.usdt_url, "! Exiting.")
            sys.exit(1)

        self._send_initial_ping()  # https://github.com/bybit-exchange/pybit/issues/164

        self.connecting = False

    def _on_open(self):
        self.logger.info("### Websocket Connection Opened ###")

    def _on_message(self, message):
        data = json.loads(message).get('data', {})

        # below we update our latest best (level 1) bid-ask data for the symbol in the incoming message:
        if data.get('symbol') == config.ticker_1:
            self.ticker_1_bid_ask = [
                float(data.get('bid1Price', self.ticker_1_bid_ask[0])),
                float(data.get('ask1Price', self.ticker_1_bid_ask[1]))
            ]
        elif data.get('symbol') == config.ticker_2:
            self.ticker_2_bid_ask = [
                float(data.get('bid1Price', self.ticker_2_bid_ask[0])),
                float(data.get('ask1Price', self.ticker_2_bid_ask[1]))
            ]

        self.ticker_1_mid_price = stat.mean(self.ticker_1_bid_ask)
        self.ticker_2_mid_price = stat.mean(self.ticker_2_bid_ask)

        # print(self.ticker_1_bid_ask, self.ticker_2_bid_ask)

    def _on_error(self, error):
        # log error and close wss conn
        self.logger.error(error)
        self.close()
        while self.ws.sock:
            continue

        # restart conn
        if not self.connecting:
            self._connect()

    def _on_close(self):
        self.logger.info("### Websocket Connection Closed ###")

    def _send_message(self, operation, topics):

        def prepare_sub_args(ufmt_topics):
            topic_fmt = "tickers.{symbol}"
            args = [topic_fmt.format(symbol=ticker) for ticker in ufmt_topics]
            message = json.dumps(
                {
                    'op': operation,
                    'req_id': str(uuid4()),
                    'args': args
                }
            )
            return message
        if self.ws.sock and self.ws.sock.connected:
            msg = prepare_sub_args(topics)
            self.ws.send(msg)

    def _on_pong(self):
        self._send_custom_ping()

    def _send_custom_ping(self):
        if self.ws.sock and self.ws.sock.connected:
            self.ws.send(self.custom_ping_msg)

    def _send_initial_ping(self):
        timer = threading.Timer(
            self.ping_interval, self._send_custom_ping
        )
        timer.start()
        self.logger.info("** Ping! **")

    def config_logger(self):
        # below we build a basic logger that only logs on error:
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(LOG_LEVEL)
        handler = logging.StreamHandler()
        handler.setLevel(LOG_LEVEL)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def subscribe_feed(self, topics: list):
        self._send_message('subscribe', topics)

    def unsubscribe_feed(self, topics: list):
        self._send_message('unsubscribe', topics)
        print(f"Successfully unthubscribed from {topics}.")

    def close(self):
        # below we block the calling thread (main thread here) until the WebSocket thread finishes all its tasks
        # (e.g. handling the closing handshake with the Bybit server):
        if self.ws.sock and self.ws.sock.connected:
            self.ws.close()
            if self.ws_thread and self.ws_thread.is_alive():
                self.ws_thread.join()
        print("Connection closed grathefully.")


ws_conn = WebSocket()
