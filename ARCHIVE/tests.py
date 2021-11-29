from connectors import Pair
from context import TraderJoeClient

print(Pair(token0_symbol='MIM', token1_symbol='TIME', context=TraderJoeClient()).id)