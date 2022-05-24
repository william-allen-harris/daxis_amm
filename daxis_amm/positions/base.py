"""
Module defining the base position abstract class.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BasePosition(ABC):
    @abstractmethod
    def tv(self, value_date, simulator, return_type):
        pass

    @abstractmethod
    def pnl(self, value_date):
        pass
