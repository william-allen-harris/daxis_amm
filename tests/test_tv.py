from daxis_amm.calculations.montecarlo import BrownianMotion
from daxis_amm.enums import Stables
from daxis_amm.graphs.GetFrames import GetIDs
from daxis_amm.positions.uniswap_v3 import UniswapV3LP
import datetime
import logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.ERROR)


ids = GetIDs(10,0)

for id in ids:
    start = datetime.datetime(2021,12, 29)
    end = datetime.datetime(2021, 12, 30)

    lp = UniswapV3LP(id, 1000, start, end, 0.1, 0.1)
    print(f"Trying to calculate {lp} ....")
    value_date = datetime.datetime(2021,12,30)
    theoretical_value = lp.tv(value_date, simulator=BrownianMotion(), return_type='breakdown')
    print(theoretical_value.mean())
