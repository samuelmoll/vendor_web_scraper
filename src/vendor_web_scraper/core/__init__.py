"""Core components of the vendor web scraper."""

from .scraper_base import BaseScraper, ScrapingResult
from .product_model import ProductInfo
from .scraper_factory import ScraperFactory, get_scraper

__all__ = [
    "BaseScraper",
    "ScrapingResult", 
    "ProductInfo",
    "ScraperFactory",
    "get_scraper",
]
