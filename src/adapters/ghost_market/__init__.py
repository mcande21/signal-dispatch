"""GHOST MARKET data source adapters -- Signal Dispatch local copy.

Copied from prediction-markets project. Import paths adapted for src.adapters.* namespace.
"""

from .agsi import AgsiAdapter
from .bonbast import BonbastAdapter
from .cloudflare_radar import CloudflareRadarAdapter
from .comtrade import ComtradeAdapter
from .dolarvzla import DolarVzlaAdapter
from .ecb import EcbAdapter
from .eia import EiaAdapter
from .eia_grid import EiaGridAdapter
from .entsog import EntsogAdapter
from .gdelt import GdeltAdapter
from .ofac import OfacAdapter
from .ooni import OoniAdapter
from .oryx import OryxAdapter
from .tedpix import TedpixAdapter
from .usaspending import UsaSpendingAdapter
from .viirs import ViirsAdapter
from ..base import GhostMarketAdapter, GhostMarketApiError

__all__ = [
    "AgsiAdapter",
    "BonbastAdapter",
    "CloudflareRadarAdapter",
    "ComtradeAdapter",
    "DolarVzlaAdapter",
    "EcbAdapter",
    "EiaAdapter",
    "EiaGridAdapter",
    "EntsogAdapter",
    "GdeltAdapter",
    "GhostMarketAdapter",
    "GhostMarketApiError",
    "OfacAdapter",
    "OoniAdapter",
    "OryxAdapter",
    "TedpixAdapter",
    "UsaSpendingAdapter",
    "ViirsAdapter",
]
