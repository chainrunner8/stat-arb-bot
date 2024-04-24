
import requests
import base64
import hashlib
import hmac
import time
from urllib.parse import urlencode
from configExecution import config


class SessionPrivate:

    def __init__(self):
        self.rest_url = config.rest_url
        self.api_key = config.api_key
        self.api_secret = config.api_secret

        self.use_nonce = True
        self.nonce = 0

    def sign_message(self, endpoint, post_data, nonce=""):
        # step 1: concatenate postData, nonce + endpoint
        message = post_data + nonce + endpoint

        # step 2: hash the result of step 1 with SHA256
        sha256_hash = hashlib.sha256(message.encode('utf8'))
        hash_digest = sha256_hash.digest()

        # step 3: base64 decode apiPrivateKey
        secret_decoded = base64.b64decode(self.api_secret)

        # step 4: use result of step 3 to hash the result of step 2 with HMAC-SHA512
        hmac_digest = hmac.new(secret_decoded, hash_digest, hashlib.sha512).digest()

        # step 5: base64 encode the result of step 4 and return
        return base64.b64encode(hmac_digest)

    # creates a unique nonce
    def get_nonce(self):
        # https://en.wikipedia.org/wiki/Modulo_operation
        self.nonce = (self.nonce + 1) & 8191
        return str(int(time.time() * 1000)) + str(self.nonce).zfill(4)

    # sends an HTTP request
    def make_request(self, request_type, endpoint, post_url="", post_body=""):
        # create authentication headers
        post_data = post_url + post_body

        if self.use_nonce:
            nonce = self.get_nonce()
            signature = self.sign_message(endpoint, post_data, nonce=nonce)
            authent_headers = {"APIKey": self.api_key, "Nonce": nonce, "Authent": signature}
        else:
            signature = self.sign_message(endpoint, post_data)
            authent_headers = {"APIKey": self.api_key, "Authent": signature}

        authent_headers["User-Agent"] = "stat-bot"

        # create request
        if post_url != "":
            url = self.rest_url + '/derivatives' + endpoint + "?" + post_url
        else:
            url = self.rest_url + '/derivatives' + endpoint

        response = requests.request(request_type, url, data=post_body.encode('utf-8'), headers=authent_headers)

        return response

    # places an order
    def send_order(self, order):
        endpoint = "/api/v3/sendorder"
        post_body = urlencode(order)
        return self.make_request("POST", endpoint, post_body=post_body)

    # cancels all open orders
    def cancel_all_orders(self, ticker=None):
        endpoint = "/api/v3/cancelallorders"
        if ticker:
            post_body = f"symbol={ticker}"
        else:
            post_body = ""
        return self.make_request("POST", endpoint, post_body=post_body)

    # sets max leverage for a market - sets margin to isolated
    def set_leverage(self, ticker):
        endpoint = "/api/v3/leveragepreferences"
        post_body = f"maxLeverage=1&symbol={ticker}"
        return self.make_request("PUT", endpoint, post_body=post_body)

    # fetches all open positions
    def get_open_positions(self):
        endpoint = "/api/v3/openpositions"
        return self.make_request("GET", endpoint)

    # fetches all open orders
    def get_open_orders(self):
        endpoint = "/api/v3/openorders"
        return self.make_request("GET", endpoint)
