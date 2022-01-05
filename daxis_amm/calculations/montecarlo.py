"""
Module defining Montecarlo calculations. Used for simulating price returns.
"""
import numpy as np
import pandas as pd
import math


class MonteCarlo:
    def __init__(self, num_simulations=100000):
        self.num_simulations = num_simulations

    def sim(self, input_ohlc: pd.DataFrame, predicted_days: int):
        ohlc = input_ohlc.copy()
        ohlc["returns"] = ohlc.Close.pct_change()
        ohlc.dropna(inplace=True)

        returns = ohlc["returns"]
        prices = ohlc["Close"].values

        last_price = prices[-1]
        simulations = {}

        # Create Each Simulation as a Column in df
        for x in range(self.num_simulations):
            count = 0
            daily_vol = returns.std()

            price_series = [last_price]

            # Series for Preditcted Days
            for i in range(predicted_days):
                price = price_series[count] * (1 + np.random.normal(0, daily_vol))
                price_series.append(price)
                count += 1

            simulations[x] = price_series

        return simulations


class BrownianMotion:
    def __init__(self, num_simulations=1000):
        self.num_simulations = num_simulations

    def sim(self, input_ohlc: pd.DataFrame, predicted_days: int):
        ohlc = input_ohlc.copy()
        ohlc["returns"] = ohlc.Close.pct_change()
        ohlc.dropna(inplace=True)

        returns = ohlc["returns"]
        self.prices = ohlc["Close"].values

        last_price = self.prices[-1]

        # Note we are assuming drift here
        simulations = {}

        # Create Each Simulation as a Column in df
        for x in range(self.num_simulations):

            # Inputs
            count = 0
            avg_daily_ret = returns.mean()
            variance = returns.var()

            daily_vol = returns.std()
            daily_drift = avg_daily_ret - (variance / 2)
            drift = daily_drift - 0.5 * daily_vol ** 2

            # Append Start Value
            prices = []

            shock = drift + daily_vol * np.random.normal()
            last_price * math.exp(shock)
            prices.append(last_price)

            for i in range(predicted_days):
                shock = drift + daily_vol * np.random.normal()
                price = prices[count] * math.exp(shock)
                prices.append(price)

                count += 1

            simulations[x] = prices

        return simulations
