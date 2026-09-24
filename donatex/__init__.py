"""A library that provides a Python interface to the DonateX API"""

__author__ = "ZetGoHack"
__license__ = "MIT"
__version__ = "0.0.11"

from .client import Client
from . import errors, types

__all__ = ["Client", "errors", "types"]
