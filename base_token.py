from dataclasses import dataclass
from abc import ABC, abstractproperty

from gql import Client


@dataclass
class ABCContext(ABC):
    client: Client


@dataclass
class ABCToken(ABC):
    symbol: str
    context: ABCContext
    
    @abstractproperty
    def id(self) -> str:
        pass 

    @abstractproperty
    def name(self) -> str:
        pass

    @abstractproperty
    def decimals(self) -> int:
        pass