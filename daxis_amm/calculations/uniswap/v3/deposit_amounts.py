"""
Module defining the Uniswap V3 Deposit Amount Calculators.
"""
from dataclasses import dataclass
from datetime import datetime
from daxis_amm.calculations.base import BaseCalculator
from daxis_amm.graphs.uniswap.v3.graph import UniswapV3Graph
from daxis_amm.calculations.uniswap.v3 import utils


@dataclass
class UniswapV3DepositAmountsCalculator(BaseCalculator):
    date: int

    def get_data(self):

        start = self.date - (1 * 60 * 60)

        funcs = {
            "token0_hour_usd_price_df": UniswapV3Graph.get_token_hour_data_info(self.position.pool.token_0.id, start, self.date),
            "token1_hour_usd_price_df": UniswapV3Graph.get_token_hour_data_info(self.position.pool.token_1.id, start, self.date),
            "ohlc_hour_df": UniswapV3Graph.get_pool_hour_data_info(self.position.pool.id, start, self.date),
            "pool_dynamic_data": UniswapV3Graph.get_dynamic_pool_info(self.position.pool.id),
        }

        return UniswapV3Graph.run(funcs)

    def stage_data(self, data):

        if datetime.now().timestamp() - self.date < 60:
            raise NotImplementedError
            # logging.info("Calculating Uniswap V3 Deposit Amount as Latest time.")
            # if 0.0 in (data["pool_dynamic_data"]["t0derivedETH"], data["pool_dynamic_data"]["t1derivedETH"]):
            #    raise Exception("Unable to calcualte deposit amounts; One of the Pool derivedETH values are Zero.")

            # price = data["pool_dynamic_data"]["token0Price"]
            # token_0_lowerprice = price * (1 - self.position.min_percentage)
            # token_0_upperprice = price * (1 + self.position.max_percentage)

            # usd_x = data["pool_dynamic_data"]["ethPriceUSD"] * data["pool_dynamic_data"]["t0derivedETH"]
            # usd_y = data["pool_dynamic_data"]["ethPriceUSD"] * data["pool_dynamic_data"]["t1derivedETH"]

        else:
            data["token0_hour_usd_price_df"] = data["token0_hour_usd_price_df"].set_index("psUnix")
            data["token1_hour_usd_price_df"] = data["token1_hour_usd_price_df"].set_index("psUnix")
            data["ohlc_hour_df"] = data["ohlc_hour_df"].set_index("psUnix")

            price = data["ohlc_hour_df"].loc[self.date]["Close"]
            token_0_lowerprice = price * (1 - self.position.min_percentage)
            token_0_upperprice = price * (1 + self.position.max_percentage)

            usd_x = data["token0_hour_usd_price_df"].loc[self.date]["Close"]
            usd_y = data["token1_hour_usd_price_df"].loc[self.date]["Close"]

        return {
            "price_current": 1 / price,
            "price_high": 1 / token_0_lowerprice,
            "price_low": 1 / token_0_upperprice,
            "price_usd_x": usd_x,
            "price_usd_y": usd_y,
            "target_amounts": self.position.amount,
        }

    def calculation(self, staged_data):
        result = utils.get_deposit_amounts(**staged_data)
        if result[0] < 0.0 or result[1] < 0.0:
            raise Exception("Unable to calculate deposit amounts; either amount0 and amount1 is below 0.0")
        return result
