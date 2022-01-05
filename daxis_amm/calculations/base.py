"Abstract Classes for Calculations."
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class BaseABC(ABC):
    "Abstract Method for Calculations."

    @abstractmethod
    def _get_data(self):
        "Get data and assign it to self._data."

    @abstractmethod
    def _stage_data(self):
        "Stage data and assign it to self.__staged_data."

    @abstractmethod
    def _calculation(self):
        "Calculate the calculation and assign it to self._result."


class BaseCalculator(BaseABC, BaseModel):
    "Base Calcuatlor."
    position: Any
    data: Any = None
    staged_data: Any = None
    result: Any = None

    def _get_data(self):
        pass

    def _stage_data(self):
        pass

    def _calculation(self):
        pass

    @property
    def run(self):
        "Get the result of the Calculation."
        self._get_data()
        self._stage_data()
        self._calculation()
        return self.result
