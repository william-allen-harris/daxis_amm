# daxis_amm

1. Create a pricing engine which estimates Uniswap V3 Liquidity Positions -> https://uniswap.org/whitepaper-v3.pdf
2. Extend for other DeFi products to identify attactive risk-adjusted return LPs.

Example:

```
>>> from daxis_amm.positions.uniswap_v3 import UniswapV3LP
>>> from datetime import datetime
>>> lp = UniswapV3LP("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", 10000, datetime(2022, 5, 1), datetime(2022, 5, 2), 0.1, 0.1)
>>> lp.tv(datetime(2022,5,2))
TV    8147.545661
dtype: float64
>>> lp.pnl(datetime(2022,5,2))
Fees USD                166.045759
Deposit Amounts USD    9774.819392
PnL                     -59.134849
dtype: float64
```


Requirements for Development:
1. Vscode - https://code.visualstudio.com/Download
2. Docker - https://www.docker.com/

All developement is compelted inside of a docker container within vscode.
Please see https://code.visualstudio.com/docs/remote/containers for more information.


TODO:

Backtesting:

1. Data -> get data from a specific date
2. Add a Backtest function to instrument class


Overall
1. Add a Portfolio Class which allows for multiple Positions to be TV at the same time.

Uniswap v3 Pricing
1. Add integration for Non-Stable coin pools. e.g WBTCWETH -> Current issue is discounding the LP returned deposit amounts in USDs. Might have to simulate ETHUSD pair prices.
