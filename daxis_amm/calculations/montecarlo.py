"""
Module defining Montecarlo calculations.
"""
import typing as _tp

import numpy as _np
import pandas as _pd


class MonteCarlo:
    def __init__(self, num_steps: int = 24, num_sims: int = 10000, seed: _tp.Optional[int] = None):
        """
        Initialize a MonteCarlo object.

        :param num_steps: Number of steps in the simulation. Default is 24.
        :type num_steps: int
        :param num_sims: Number of simulations to run. Default is 10000.
        :type num_sims: int
        :param seed: Random seed for reproducibility. Default is None.
        :type seed: Optional[int]
        """
        self.num_steps = num_steps
        self.num_sims = num_sims
        self.seed = seed

    def sim(self, current_price: float, r: float, vol: float, T: float) -> _pd.DataFrame:
        """
        Run a Monte Carlo simulation.

        :param current_price: Current price of the asset.
        :type current_price: float
        :param r: Risk-free interest rate.
        :type r: float
        :param vol: Volatility of the asset.
        :type vol: float
        :param T: Time period of the simulation.
        :type T: float
        :return: DataFrame containing the simulation results.
        :rtype: pandas.DataFrame
        """
        if self.seed is not None:
            _np.random.seed(self.seed)

        delta_t = T / self.num_steps
        simulations = _np.zeros((self.num_steps, self.num_sims))
        simulations[0] = current_price

        for i in range(0, self.num_steps - 1):
            w = _np.random.standard_normal(self.num_sims)
            simulations[i + 1] = simulations[i] * (1 + r * delta_t + vol * _np.sqrt(delta_t) * w)

        return _pd.DataFrame(simulations)
