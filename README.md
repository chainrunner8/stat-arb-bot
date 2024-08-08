(# stat-arb-bot
A statistical arbitrage bot that runs on the Bybit centralised exchange.

All the code for this bot is original and written by myself. I uploaded the initial version in April 2024 which traded on Kraken Futures, but most cryptos were highly illiquid on there, so I had to switch over to Bybit which simulates demo trading orders in a real orderbook. We want to first test our bot with mock money but in a real trading environment, so for that reason Bybit was a much better choice.
I chose not to use the WebSocket() class of the pybit library as it doesn't allow you to unsubscribe from a websocket topic - leaving you with the only option to close the wss connection and reopen it to change topics, which I don't find elegant nor efficient. Therefore I coded my own websocket class that connects to the Bybit websocket api and allows me to unsubscribe from a topic.

This version of the bot is fully functional as of August 2024 but doesn't have any real edge, this is something I'm working on by perfecting the strategy and tuning the execution parameters. Should I find a way to make serious money with this bot, of course I won't upload it on here!

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
