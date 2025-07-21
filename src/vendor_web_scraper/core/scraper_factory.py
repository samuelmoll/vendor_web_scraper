"""
Factory for creating vendor-specific scrapers.
"""

import logging
from typing import Dict, Type, Optional, List
from urllib.parse import urlparse

from .scraper_base import BaseScraper


class ScraperFactory:
    """
    Factory class for creating appropriate scrapers based on URLs or vendor names.

    This factory maintains a registry of available scrapers and can automatically
    select the appropriate scraper for a given URL or vendor.
    """

    def __init__(self):
        self._scrapers: Dict[str, Type[BaseScraper]] = {}
        self._domain_mapping: Dict[str, str] = {}
        self.logger = logging.getLogger(__name__)

    def register_scraper(
        self, vendor_name: str, scraper_class: Type[BaseScraper], domains: Optional[List[str]] = None
    ) -> None:
        """
        Register a scraper class for a specific vendor.

        Args:
            vendor_name: Name of the vendor (e.g., "rs_components")
            scraper_class: Scraper class that inherits from BaseScraper
            domains: List of domains this scraper handles
        """
        if not issubclass(scraper_class, BaseScraper):
            raise TypeError("Scraper class must inherit from BaseScraper")

        self._scrapers[vendor_name.lower()] = scraper_class

        # Register domain mappings
        if domains:
            for domain in domains:
                self._domain_mapping[domain.lower()] = vendor_name.lower()

        self.logger.info(f"Registered scraper for {vendor_name}")

    def get_scraper_by_vendor(self, vendor_name: str, **kwargs) -> Optional[BaseScraper]:
        """
        Get scraper instance by vendor name.

        Args:
            vendor_name: Name of the vendor
            **kwargs: Additional arguments to pass to scraper constructor

        Returns:
            Scraper instance or None if not found
        """
        vendor_key = vendor_name.lower()

        if vendor_key not in self._scrapers:
            self.logger.warning(f"No scraper registered for vendor: {vendor_name}")
            return None

        scraper_class = self._scrapers[vendor_key]

        try:
            return scraper_class(**kwargs)
        except Exception as e:
            self.logger.error(f"Failed to create scraper for {vendor_name}: {e}")
            return None

    def get_scraper_by_url(self, url: str, **kwargs) -> Optional[BaseScraper]:
        """
        Get appropriate scraper for a given URL.

        Args:
            url: Product URL to scrape
            **kwargs: Additional arguments to pass to scraper constructor

        Returns:
            Scraper instance or None if no suitable scraper found
        """
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()

            # Remove www. prefix if present
            if domain.startswith("www."):
                domain = domain[4:]

            # Look for exact domain match
            if domain in self._domain_mapping:
                vendor_name = self._domain_mapping[domain]
                return self.get_scraper_by_vendor(vendor_name, **kwargs)

            # Look for partial domain matches
            for registered_domain, vendor_name in self._domain_mapping.items():
                if domain.endswith(registered_domain) or registered_domain.endswith(domain):
                    return self.get_scraper_by_vendor(vendor_name, **kwargs)

            self.logger.warning(f"No scraper found for domain: {domain}")
            return None

        except Exception as e:
            self.logger.error(f"Error parsing URL {url}: {e}")
            return None

    def get_available_vendors(self) -> List[str]:
        """
        Get list of all registered vendor names.

        Returns:
            List of vendor names
        """
        return list(self._scrapers.keys())

    def get_supported_domains(self) -> Dict[str, str]:
        """
        Get mapping of supported domains to vendor names.

        Returns:
            Dictionary mapping domains to vendor names
        """
        return self._domain_mapping.copy()

    def is_url_supported(self, url: str) -> bool:
        """
        Check if URL is supported by any registered scraper.

        Args:
            url: URL to check

        Returns:
            True if URL is supported
        """
        return self.get_scraper_by_url(url) is not None


# Global factory instance
factory = ScraperFactory()


def register_scraper(vendor_name: str, scraper_class: Type[BaseScraper], domains: Optional[List[str]] = None) -> None:
    """
    Convenience function to register a scraper with the global factory.

    Args:
        vendor_name: Name of the vendor
        scraper_class: Scraper class
        domains: List of domains this scraper handles
    """
    factory.register_scraper(vendor_name, scraper_class, domains)


def get_scraper(vendor_name_or_url: str, **kwargs) -> Optional[BaseScraper]:
    """
    Convenience function to get a scraper by vendor name or URL.

    Args:
        vendor_name_or_url: Either vendor name or product URL
        **kwargs: Additional arguments for scraper constructor

    Returns:
        Scraper instance or None
    """
    # Check if it's a URL
    if vendor_name_or_url.startswith(("http://", "https://")):
        return factory.get_scraper_by_url(vendor_name_or_url, **kwargs)
    else:
        return factory.get_scraper_by_vendor(vendor_name_or_url, **kwargs)
