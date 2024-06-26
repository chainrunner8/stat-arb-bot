# stat-arb-bot
A statistical arbitrage bot that runs on the Kraken centralised exchange.

Except for the message signing and request sending functions in sessionPrivate.py that were taken from the Kraken API documentation by Crypto Facilities Ltd, all the code for this bot is original and written by myself.

This version of the bot is fully functional as of April 2024 but doesn't have any real edge, this is something I'm working on by perfecting the strategy and tuning the execution parameters. Should I find a way to make serious money with this bot, of course I won't upload it on here!

The strategy folder contains the modules that:
- fetch historical price data for all tradeable symbols on Kraken Futures,
- run the Engle-Granger cointegration test on all possible pairs of symbols,
- single out the pairs with a statistically significant cointegration relationship,
- keep the pairs that both have among the lowest p-values and highest numbers of zero-crossings over the lookback period studied.

The execution folder contains the bot itself that manages trades according to the parameters dictated by the strategy. These parameters can be tuned in configExecution.py and the changes will reflect across all the execution modules. 

In order to run this bot in your local host, first create a Stat Bot parent folder and inside it two folders: 
- a Programs folder containing:
  - the Strategy folder,
  - the Execution folder,
  - a .env file with your Kraken Futures and/or Demo API keys.
- a Data folder that will contain the strategy data i.e. historical_prices.json, instruments.json and a Pairs folder (that you should create) that will contain the Z-score series of the latest best pairs to trade.
