""" The WebSocket and HTTP API code on the demo environment is identical to
the live production code in terms of the feeds/endpoints and the response
structure. """


class StratConfig:
    def __init__(self, lookback, stat_sig):
        self.resolution = str()
        self.lookback = lookback
        self.stat_sig = stat_sig

        if self.stat_sig == 0.01: # 1% = 0 ; 5% = 1 ; 10% = 2
            self.stat_sig_index = 0
        elif self.stat_sig == 0.05:
            self.stat_sig_index = 1
        else:
            self.stat_sig_index = 2


config = StratConfig(lookback=200, stat_sig=0.05)
