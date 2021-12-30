"""
Module defining Montecarlo calculations. Used for simulating price returns.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import style
from scipy.stats import norm
import math


class MonteCarlo:
    def __init__(self, num_simulations=100000, predicted_days=24):
        self.num_simulations = num_simulations
        self.predicted_days = predicted_days
        self.simulation_df = pd.DataFrame()
        self.simulations_dict = dict()

    def sim(self, input_ohlc):
        ohlc = input_ohlc.copy()
        ohlc["returns"] = ohlc.Close.pct_change()
        ohlc.dropna(inplace=True)

        returns = ohlc["returns"]
        self.prices = ohlc["Close"].values

        last_price = self.prices[-1]
        simulations = {}

        # Create Each Simulation as a Column in df
        for x in range(self.num_simulations):
            count = 0
            daily_vol = returns.std()

            price_series = [last_price]

            # Series for Preditcted Days
            for i in range(self.predicted_days):
                price = price_series[count] * (1 + np.random.normal(0, daily_vol))
                price_series.append(price)
                count += 1

            simulations[x] = price_series

        self.simulations_dict = simulations
        # import json
        # with open('tests/data/simulation_df.json', 'w') as f:
        #    json.dump(simulations, f)
        self.simulation_df = pd.DataFrame(simulations)

    def line_graph(self):
        prices = self.prices
        predicted_days = self.predicted_days
        simulation_df = self.simulation_df

        last_price = prices[-1]
        fig = plt.figure()
        style.use("bmh")

        title = "Monte Carlo Simulation: " + str(predicted_days) + " Days"
        plt.plot(simulation_df)
        fig.suptitle(title, fontsize=18, fontweight="bold")
        plt.xlabel("Day")
        plt.ylabel("Price ($USD)")
        plt.grid(True, color="grey")
        plt.axhline(y=last_price, color="r", linestyle="-")
        plt.show()

    def histogram(self):
        simulation_df = self.simulation_df

        ser = simulation_df.iloc[-1, :]
        x = ser
        mu = ser.mean()
        sigma = ser.std()

        num_bins = 20
        # the histogram of the data
        n, bins, patches = plt.hist(x, num_bins, density=True, stacked=True, facecolor="blue", alpha=0.5)

        # add a 'best fit' line
        y = norm.pdf(bins, mu, sigma)
        plt.plot(bins, y, "r--")
        plt.xlabel("Price")
        plt.ylabel("Probability")
        plt.title(r"Histogram of Speculated Stock Prices", fontsize=18, fontweight="bold")

        # Tweak spacing to prevent clipping of ylabel
        plt.subplots_adjust(left=0.15)
        plt.show()

    def VaR(self):
        simulation_df = self.simulation_df
        prices = self.prices

        last_price = prices[-1]

        price_array = simulation_df.iloc[-1, :]
        price_array = sorted(price_array, key=int)
        var = np.percentile(price_array, 1)

        val_at_risk = last_price - var
        print("Value at Risk: ", val_at_risk)

        # Histogram
        fit = norm.pdf(price_array, np.mean(price_array), np.std(price_array))
        plt.plot(price_array, fit, "-o")
        plt.hist(price_array, density=True, stacked=True)
        plt.xlabel("Price")
        plt.ylabel("Probability")
        plt.title(r"Histogram of Speculated Stock Prices", fontsize=18, fontweight="bold")
        plt.axvline(x=var, color="r", linestyle="--", label="Price at Confidence Interval: " + str(round(var, 2)))
        plt.axvline(x=last_price, color="k", linestyle="--", label="Current Stock Price: " + str(round(last_price, 2)))
        plt.legend(loc="upper right")
        plt.show()


class BrownianMotion(MonteCarlo):
    def __init__(self, num_simulations=1000, predicted_days=24):
        self.num_simulations = num_simulations
        self.predicted_days = predicted_days
        self.simulation_df = pd.DataFrame()
        self.simulations_dict = dict()

    def sim(self, input_ohlc):
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

            for i in range(self.predicted_days):
                shock = drift + daily_vol * np.random.normal()
                price = prices[count] * math.exp(shock)
                prices.append(price)

                count += 1

            simulations[x] = prices
        
        self.simulations_dict = simulations
        self.simulation_df = pd.DataFrame(simulations)
