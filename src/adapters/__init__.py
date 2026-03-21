"""Signal Dispatch adapter package.

Local copies of data source adapters -- fully self-contained.
No subprocess calls to prediction-markets project.
"""

from .base import GhostMarketAdapter, GhostMarketApiError
from .fred import FredAdapter
from .kalshi import KalshiAdapter
from .noaa import NoaaAdapter
from .ghost_market import (
    AgsiAdapter,
    BonbastAdapter,
    CloudflareRadarAdapter,
    ComtradeAdapter,
    DolarVzlaAdapter,
    EcbAdapter,
    EiaAdapter,
    EiaGridAdapter,
    EntsogAdapter,
    GdeltAdapter,
    OfacAdapter,
    OoniAdapter,
    OryxAdapter,
    TedpixAdapter,
    UsaSpendingAdapter,
    ViirsAdapter,
)
from .osint import FederalRegisterAdapter, CongressAdapter, FecAdapter
from .acled import AcledAdapter
from .adsb import AdsbAdapter
from .census import CensusAdapter
from .opensanctions import OpenSanctionsAdapter
from .telegram_osint import TelegramOsintAdapter
from .cps_voting import CpsVotingAdapter
from .elections import ElectionsAdapter

__all__ = [
    "GhostMarketAdapter",
    "GhostMarketApiError",
    "FredAdapter",
    "KalshiAdapter",
    "NoaaAdapter",
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
    "OfacAdapter",
    "OoniAdapter",
    "OryxAdapter",
    "TedpixAdapter",
    "UsaSpendingAdapter",
    "ViirsAdapter",
    "FederalRegisterAdapter",
    "CongressAdapter",
    "FecAdapter",
    "AcledAdapter",
    "AdsbAdapter",
    "CensusAdapter",
    "OpenSanctionsAdapter",
    "TelegramOsintAdapter",
    "CpsVotingAdapter",
    "ElectionsAdapter",
]
