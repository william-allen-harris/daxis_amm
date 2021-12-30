"Module for all Enums."
from enum import Enum


class Stables(Enum):
    "Stable coin symbols."
    USDC = "USDC"
    USDT = "USDT"
    DAI = "DAI"
    BUSD = "BUSD"
    UST = "UST"
    TUSD = "TUSD"
    USDP = "USDP"
    USDN = "USDN"
    FEI = "FEI"
    FRAX = "FRAX"

    @classmethod
    def has_member_key(cls, key):
        "Evaluate if the Enum has the key"
        return key in cls.__members__
