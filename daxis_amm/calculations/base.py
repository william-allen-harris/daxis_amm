"Abstract Classes for Calculations."
import abc as _abc
import dataclasses as _dc

from toolz import pipe as _pipe

from daxis_amm.positions.base import BasePosition as _BasePosition


@_dc.dataclass
class BaseCalculator(_abc.ABC):
    position: _BasePosition

    "Abstract Method for Calculations."

    @_abc.abstractmethod
    def get_data(self):
        "Get data for the calculator from a graph class."

    @_abc.abstractmethod
    def stage_data(self, data):
        "Stage data the data which will be used in in the calculation."

    @_abc.abstractmethod
    def calculation(self, staged_data):
        "Calculate the result."

    def run(self):
        "Run all of the components in the calculator and return the result."
        return _pipe(self.get_data(), self.stage_data, self.calculation)
