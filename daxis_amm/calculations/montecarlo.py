"""
Module defining Montecarlo calculations.
"""
import numpy as np

from typing import Optional


class MonteCarlo:
    def __init__(self, num_steps: int = 256, num_sims: int = 100000, seed: Optional[int] = None):
        self.num_steps = num_steps
        self.num_sims = num_sims
        self.seed = seed

    def sim(self, current_price: float, r: float, vol: float, T: float):
        if self.seed is not None:
            np.random.seed(self.seed)

        delta_t = T / self.num_steps
        simulations = np.zeros((self.num_steps, self.num_sims))
        simulations[0] = current_price

        for i in range(0, self.num_steps - 1):
            w = np.random.standard_normal(self.num_sims)
            simulations[i + 1] = simulations[i] * (1 + r * delta_t + vol * np.sqrt(delta_t) * w)

        return simulations
