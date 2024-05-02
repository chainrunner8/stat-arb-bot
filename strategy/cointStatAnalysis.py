
import statsmodels.api as sm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import coint
from configStrategy import config


class Pair:
    def __init__(self, p_val, t_val, t_crit):
        self.symbol = ()
        self.p_val = p_val
        self.t_val = t_val
        self.t_crit = t_crit
        self.hedge_ratio = int()
        self.prices = dict()
        self.spread = list()
        self.zero_crossings = int()
        self.z_score = list()


def is_cointegrated(sym1_prices, sym2_prices):
    try:
        result = coint(sym1_prices, sym2_prices)
    except ValueError as e:
        print(e, f"Symbol 1 prices: {sym1_prices}", f"Symbol 2   prices: {sym2_prices}")
        pair = Pair(p_val=1, t_val=None, t_crit=None)
        return pair
    else:
        pair = Pair(p_val=result[1], t_val=result[0], t_crit=result[2][config.stat_sig_index])
        return pair


def get_pair_params(pair):

    # hedge ratio:
    ols = sm.OLS(pair.prices['sym1'], pair.prices['sym2']).fit()
    pair.hedge_ratio = ols.params[0]

    # spread:
    pair.spread = list(pd.Series(pair.prices['sym1']) - pd.Series(pair.prices['sym2']) * pair.hedge_ratio)

    # z-scores:
    df_spread = pd.DataFrame(list(pair.spread), columns=["spread"])

    mean = df_spread.rolling(window=config.z_window).mean()
    std = df_spread.rolling(window=config.z_window).std()

    df_spread["z_score"] = (df_spread - mean) / std

    # zero crossings:
    pair.z_score = df_spread["z_score"].astype(float).values  # kind of useless line
    pair.zero_crossings = len(np.nonzero(np.diff(np.sign(pair.z_score)))[0])  # obtained by counting the number of times the Z-score changes sign

    return pair


def get_coint_pairs(data):
    coint_pairs = []
    counter = 0
    # TODO: loop through data and return coint pairs
    symbols = list(data.keys())
    for symbol_1 in symbols:
        sym1_prices = data[symbol_1]
        for symbol_2, value in data.items():
            if symbol_2 == symbol_1:
                continue
            else:
                sym2_prices = data[symbol_2]
                pair = is_cointegrated(sym1_prices, sym2_prices)

                # only save pair if statistically significant:
                if pair.p_val <= config.stat_sig:
                    pair.symbol = (symbol_1, symbol_2)
                    pair.prices = {'sym1': sym1_prices, 'sym2': sym2_prices}
                    coint_pairs.append(pair)
                    counter += 1
                    print(f"Found {counter} pair.")
        # no need to check duplicate pairs so drop that symbol from the dict:
        del data[symbol_1]

    return coint_pairs


def to_dataframe(coint_pairs):

    for pair in coint_pairs:
        pair = get_pair_params(pair)
    df_pairs = pd.DataFrame([vars(pair) for pair in coint_pairs], columns=list(vars(coint_pairs[0]).keys()))
    df_pairs = df_pairs.sort_values("zero_crossings", ascending=False)

    return df_pairs


def plot_trends(dataframe):
    pair = dataframe.iloc[0]
    # plot trends:
    fig, axs = plt.subplots(2, figsize=(16, 8))
    fig.suptitle(f"Spread & Z-score - {pair.symbol[0]} vs {pair.symbol[1]}")
    axs[0].plot(pair.spread)
    axs[1].plot(pair.z_score)
    plt.show()


def save_for_backtest(dataframe):
    for i in range(5):
        row = dataframe.iloc[i]
        df_backtest = pd.DataFrame()
        df_backtest['sym1_prices'] = row.prices['sym1']
        df_backtest['sym2_prices'] = row.prices['sym2']
        df_backtest['spread'] = row.spread
        df_backtest['z_score'] = row.z_score
        sym1 = row.symbol[0].split('PF_')[1]
        sym2 = row.symbol[1].split('PF_')[1]

        df_backtest.to_excel(f"../../Data/Pairs/pair{i}_{sym1}-{sym2}_data.xlsx", index=False)
