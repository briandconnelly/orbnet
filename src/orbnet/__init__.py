from importlib.metadata import version

__version__ = version("orbnet")


from .client import OrbAPIClient
from .models import (
    AllDatasetsResponse,
    ResponsivenessRecord,
    ScoreRecord,
    SpeedRecord,
    WebResponsivenessRecord,
)

__all__ = [
    "OrbAPIClient",
    "ScoreRecord",
    "ResponsivenessRecord",
    "WebResponsivenessRecord",
    "SpeedRecord",
    "AllDatasetsResponse",
]
