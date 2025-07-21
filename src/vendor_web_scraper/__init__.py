"""
Vendor Web Scraper Package

A modular, extensible framework for scraping product information from vendor websites
with support for multiple output formats including InvenTree import.
"""

__version__ = "0.1.0"
__author__ = "Decoda Platform"

from .core.scraper_base import BaseScraper, ScrapingResult
from .core.product_model import ProductInfo
from .core.scraper_factory import ScraperFactory
from .exporters.base_exporter import BaseExporter
from .exporters.inventree_exporter import InvenTreeExporter
from .exporters.excel_exporter import ExcelExporter

__all__ = [
    "BaseScraper",
    "ScrapingResult",
    "ProductInfo",
    "ScraperFactory",
    "BaseExporter",
    "InvenTreeExporter",
    "ExcelExporter",
]
