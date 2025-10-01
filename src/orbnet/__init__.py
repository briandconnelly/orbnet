from importlib.metadata import version

__version__ = version("orbnet")


from .client import OrbAPIClient

__all__ = [
    "OrbAPIClient",
]
