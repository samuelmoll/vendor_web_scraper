"""
Base scraper class providing common functionality for all vendor scrapers.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

from .product_model import ProductInfo


@dataclass
class ScrapingResult:
    """Result of a scraping operation"""

    success: bool
    product_info: Optional[ProductInfo] = None
    error_message: Optional[str] = None
    response_time_ms: Optional[float] = None
    http_status_code: Optional[int] = None

    def __post_init__(self):
        """Validate the result after initialization"""
        if self.success and self.product_info is None:
            raise ValueError("Successful scraping result must include product_info")
        if not self.success and self.error_message is None:
            self.error_message = "Unknown error occurred"


class BaseScraper(ABC):
    """
    Abstract base class for vendor-specific scrapers.

    Provides common functionality like HTTP requests, error handling,
    rate limiting, and standardized interfaces that all vendor scrapers inherit.
    """

    def __init__(
        self,
        vendor_name: str,
        base_url: str,
        delay_between_requests: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3,
        custom_headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the base scraper.

        Args:
            vendor_name: Name of the vendor (e.g., "RS Components")
            base_url: Base URL of the vendor website
            delay_between_requests: Delay in seconds between requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            custom_headers: Additional HTTP headers to include
        """
        self.vendor_name = vendor_name
        self.base_url = base_url
        self.delay_between_requests = delay_between_requests
        self.timeout = timeout
        self.max_retries = max_retries

        # Set up logging
        self.logger = logging.getLogger(f"{__name__}.{vendor_name}")

        # Initialize HTTP session
        self.session = requests.Session()

        # Set up default headers
        ua = UserAgent()
        self.default_headers = {
            "User-Agent": ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        if custom_headers:
            self.default_headers.update(custom_headers)

        self.session.headers.update(self.default_headers)

        # Rate limiting
        self._last_request_time = 0

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self.delay_between_requests:
            sleep_time = self.delay_between_requests - time_since_last
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _make_request(self, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with error handling and retries.

        Args:
            url: URL to request
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            requests.RequestException: If all retry attempts fail
        """
        self._enforce_rate_limit()

        # Ensure absolute URL
        if not url.startswith(("http://", "https://")):
            url = urljoin(self.base_url, url)

        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"Making request to {url} (attempt {attempt + 1})")

                response = self.session.get(url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request attempt {attempt + 1} failed: {e}")

                if attempt == self.max_retries:
                    self.logger.error(f"All {self.max_retries + 1} attempts failed for {url}")
                    raise

                # Exponential backoff for retries
                sleep_time = (2**attempt) * self.delay_between_requests
                self.logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)

    def _parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content using BeautifulSoup.

        Args:
            html_content: Raw HTML string

        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html_content, "lxml")

    def _extract_text_safe(self, element, default: str = "") -> str:
        """
        Safely extract text from BeautifulSoup element.

        Args:
            element: BeautifulSoup element or None
            default: Default value if element is None or empty

        Returns:
            Extracted text or default value
        """
        if element is None:
            return default

        text = element.get_text(strip=True)
        return text if text else default

    def _extract_number_from_text(self, text: str) -> Optional[float]:
        """
        Extract first number from text string.

        Args:
            text: Text potentially containing numbers

        Returns:
            First number found or None
        """
        import re

        if not text:
            return None

        # Remove common currency symbols and thousands separators
        cleaned = re.sub(r"[£$€¥,]", "", text)

        # Find first number (including decimals)
        match = re.search(r"(\d+\.?\d*)", cleaned)

        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None

        return None

    def _to_lower_underscore_format(self, text: str) -> str:
        """
        Convert text to lower case with underscores.

        Args:
            text: Input string

        Returns:
            Lowercase string with spaces replaced by underscores
        """
        return text.lower().replace(" ", "_") if text else ""

    @abstractmethod
    def scrape_product(self, product_url: str) -> ScrapingResult:
        """
        Scrape product information from a given URL.

        This method must be implemented by each vendor-specific scraper.

        Args:
            product_url: URL of the product page to scrape

        Returns:
            ScrapingResult containing product information or error details
        """
        pass

    @abstractmethod
    def extract_product_info(self, soup: BeautifulSoup, url: str) -> ProductInfo:
        """
        Extract product information from parsed HTML.

        This method must be implemented by each vendor-specific scraper.

        Args:
            soup: BeautifulSoup object of the product page
            url: Original URL of the product page

        Returns:
            ProductInfo object with extracted data
        """
        pass

    def validate_url(self, url: str) -> bool:
        """
        Validate if the URL belongs to this vendor.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid for this vendor
        """
        try:
            parsed = urlparse(url)
            vendor_domain = urlparse(self.base_url).netloc
            return parsed.netloc == vendor_domain
        except Exception:
            return False

    def get_supported_domains(self) -> List[str]:
        """
        Get list of domains supported by this scraper.

        Returns:
            List of domain names
        """
        return [urlparse(self.base_url).netloc]

    def scrape_multiple_products(self, urls: List[str]) -> List[ScrapingResult]:
        """
        Scrape multiple products sequentially.

        Args:
            urls: List of product URLs to scrape

        Returns:
            List of ScrapingResult objects
        """
        results = []

        for i, url in enumerate(urls):
            self.logger.info(f"Scraping product {i + 1}/{len(urls)}: {url}")

            try:
                result = self.scrape_product(url)
                results.append(result)

                if not result.success:
                    self.logger.warning(f"Failed to scrape {url}: {result.error_message}")

            except Exception as e:
                self.logger.error(f"Unexpected error scraping {url}: {e}")
                results.append(ScrapingResult(success=False, error_message=f"Unexpected error: {str(e)}"))

        return results
