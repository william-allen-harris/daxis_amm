"""
Module defining the base position abstract class.
"""
import abc as _abc
import dataclasses as _dc


@_dc.dataclass
class BasePosition(_abc.ABC):
    """
    Base position abstract class.

    This is an abstract class that defines the interface for a position object.
    Subclasses should implement the abstract methods `tv` and `pnl`.
    """

    @_abc.abstractmethod
    def tv(self, value_date, simulator, return_type):
        """
        Calculate the total value of the position.

        :param value_date: The date at which the position value is calculated.
        :type value_date: Any
        :param simulator: The simulator object used for simulating market scenarios.
        :type simulator: Any
        :param return_type: The type of return to calculate, e.g., 'price', 'percent', etc.
        :type return_type: str
        :return: The total value of the position.
        :rtype: Any
        """

    @_abc.abstractmethod
    def pnl(self, value_date):
        """
        Calculate the profit and loss of the position.

        :param value_date: The date at which the profit and loss is calculated.
        :type value_date: Any
        :return: The profit and loss of the position.
        :rtype: Any
        """
