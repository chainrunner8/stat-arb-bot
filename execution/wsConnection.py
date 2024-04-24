
""" The WebSocket and HTTP API code on the demo environment is identical to
the live production code in terms of the feeds/endpoints and the response
structure. """

import json
import time
import sys
import websocket
import threading
import statistics as stat
from configExecution import config
from util.cfLogging import CfLogger


class WebSocket:

    def __init__(self):

        self.base_url = config.wss_url
        self.api_key = config.api_key
        self.api_secret = config.api_secret

        self.ticker_1_bid_ask = []
        self.ticker_2_bid_ask = []
        self.ticker_1_mid_price = 0
        self.ticker_2_mid_price = 0

        self.timeout = 5
        self.logger = CfLogger.get_logger("websocket-api")

        self._connect()

    def _connect(self):

        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(self.base_url,
                                         on_open=lambda ws: self._on_open(),
                                         on_message=lambda ws, message: self._on_message(message),
                                         on_error=lambda ws, error: self._on_error(error),
                                         on_close=lambda ws, close_status_code, close_msg:
                                         self._on_close(close_status_code, close_msg))
        threading.Thread(target=lambda: self.ws.run_forever(ping_interval=30)).start()
        conn_timeout = self.timeout
        while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout:
            time.sleep(1)
            conn_timeout -= 1

        if not conn_timeout:
            self.logger.info("Couldn't connect to", self.base_url, "! Exiting.")
            sys.exit(1)

    def _on_open(self):

        self.logger.info("### Websocket Connection Opened ###")

    def _on_message(self, message):

        msg_json = json.loads(message)
        if msg_json['product_id'] == config.ticker_1:
            self.ticker_1_bid_ask = [msg_json['bid'], msg_json['ask']]
        else:
            self.ticker_2_bid_ask = [msg_json['bid'], msg_json['ask']]
        self.ticker_1_mid_price = stat.mean(self.ticker_1_bid_ask)
        self.ticker_2_mid_price = stat.mean(self.ticker_2_bid_ask)

    def _on_error(self, error):

        self.logger.info(error)

    def _on_close(self, close_status_code, close_msg):

        self.logger.info("### Websocket Connection Closed ###", close_status_code, close_msg)

    def subscribe_feed(self, product_ids):

        request_message = {
            "event": "subscribe",
            "feed": "ticker",
            "product_ids": product_ids
        }
        self.ws.send(json.dumps(request_message))

    def unsubscribe_feed(self, product_ids):

        request_message = {
            "event": "unsubscribe",
            "feed": "ticker",
            "product_ids": product_ids
        }
        self.ws.send(json.dumps(request_message))


""" streaming live prices """

ws = WebSocket()

# ws.subscribe_feed()
# time.sleep(5)
# ws.unsubscribe_feed()
# time.sleep(3)
# ws.ws.close()
