# stat-arb-bot
A statistical arbitrage bot that runs on the Kraken centralised exchange.

Except for the message signing and request sending functions in sessionPrivate.py that were taken from the Kraken API documentation by Crypto Facilities Ltd, all the code for this bot is original and written by myself.

The strategy folder contains the modules that:
- fetch historical price data for all tradeable symbols on Kraken Futures,
- run the Engle-Granger cointegration test on all possible pairs of symbols,
- single out the pairs with a statistically significant cointegration relationship,
- keep the pairs that both have among the lowest p-values and highest numbers of zero-crossings over the lookback period studied.

The execution folder contains the bot itself that manages trades according to the parameters dictated by the strategy. These parameters can be tuned in configExecution.py and the changes will reflect across all the execution modules. 
In order to run this bot in your local host, a .env file should be created in the parent folder with your Kraken Futures and/or Demo API keys. The folder can be organised like so:

parent folder -- Programs  -- Strategy
             |            |
             |             -- Execution
             |            |
             |             -- .env
             |
              -- Data  -- Pairs
                      |
                       -- historical_prices.json
                      |
                       -- instruments.json
