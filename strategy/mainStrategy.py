
import json
import warnings
from cointegration import get_coint_pairs, to_dataframe, save_for_backtest
from historical_data import get_historical_prices
from config_strategy import config

warnings.simplefilter(action="ignore", category=FutureWarning)


get_historical_prices(config)

with open("../../Data/historical_prices.json") as file:
    price_data = json.load(file)

coint_pairs = get_coint_pairs(price_data)

df_pairs = to_dataframe(coint_pairs)

save_for_backtest(df_pairs)

plot_trends(df_coint_pairs)
