

class StratConfig:

    def __init__(self, timeframe, lookback, z_window, stat_sig):
        self.timeframe = timeframe
        self.lookback = lookback
        self.stat_sig = stat_sig
        self.z_window = z_window

        if self.stat_sig == 0.01:  # 1% = 0 ; 5% = 1 ; 10% = 2
            self.stat_sig_index = 0
        elif self.stat_sig == 0.05:
            self.stat_sig_index = 1
        else:
            self.stat_sig_index = 2


config = StratConfig(timeframe='1h', lookback=200, z_window=21, stat_sig=0.05)  # configuration example
