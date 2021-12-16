from connectors import LPUniswapV3
from context import UniswapV3Client
from montecarlo import MonteCarlo

lp = LPUniswapV3(deposit_amount=1000.0, token0_symbol='WETH', token1_symbol='USDT', fee_tier=500, context=UniswapV3Client(), max_perc=0.5, min_per=0.5)
lp.pool.plot_liquidity()
print(lp.tv(MonteCarlo()))