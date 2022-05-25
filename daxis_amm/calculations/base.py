"Abstract Classes for Calculations."
from abc import ABC, abstractmethod
from dataclasses import dataclass

from toolz import pipe

from daxis_amm.positions.base import BasePosition


@dataclass
class BaseCalculator(ABC):
    position: BasePosition

    "Abstract Method for Calculations."

    @abstractmethod
    def get_data(self):
        "Get data for the calculator from a graph class."

    @abstractmethod
    def stage_data(self, data):
        "Stage data the data which will be used in in the calculation."

    @abstractmethod
    def calculation(self, staged_data):
        "Calculate the result."

    def run(self):
        "Run all of the components in the calculator and return the result."
        return pipe(self.get_data(), self.stage_data, self.calculation)
