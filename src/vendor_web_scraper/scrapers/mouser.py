"""
Mouser Electronics scraper implementation.
"""

import re
import time
import logging
from decimal import Decimal
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from bs4.element import PageElement, Tag
import requests

try:
    from ..core.scraper_base import BaseScraper, ScrapingResult
    from ..core.product_model import (
        ProductInfo,
        ProductSpecifications,
        ProductPricing,
        ProductAvailability,
        ProductMedia,
    )
    from ..core.cookie_manager import MouserCookieManager
except ImportError:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    print(str(Path(__file__).resolve().parent.parent.parent))
    from vendor_web_scraper.core.scraper_base import BaseScraper, ScrapingResult
    from vendor_web_scraper.core.product_model import (
        ProductInfo,
        ProductSpecifications,
        ProductPricing,
        ProductAvailability,
        ProductMedia,
    )
    from vendor_web_scraper.core.cookie_manager import MouserCookieManager


class MouserScraper(BaseScraper):
    """
    Scraper for Mouser Electronics (mouser.com) product pages.

    Extracts product information including specifications, pricing,
    availability, and technical details from Mouser product pages.
    """

    def __init__(self, **kwargs):
        """Initialize Mouser scraper."""
        # Extract cookies and custom headers before calling super()
        mouser_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Priority": "u=0, i",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

        # Add custom headers to kwargs
        if "custom_headers" in kwargs:
            kwargs["custom_headers"].update(mouser_headers)
        else:
            kwargs["custom_headers"] = mouser_headers

        super().__init__(
            vendor_name="Mouser Electronics",
            base_url="https://au.mouser.com",
            **kwargs,
        )

        # Initialize cookie manager
        self.cookie_manager = MouserCookieManager(
            auto_refresh=kwargs.get("auto_refresh_cookies", True),
            cookie_expiry_hours=kwargs.get("cookie_expiry_hours", 12),
        )

        # Set up cookies
        self._set_mouser_cookies()

    def _set_mouser_cookies(self):
        """Set Mouser-specific cookies using the cookie manager."""
        # Get fresh cookies from the cookie manager
        cookies = self.cookie_manager.get_mouser_cookies()

        # Set cookies on the session
        for name, value in cookies.items():
            self.session.cookies.set(name, value, domain=".mouser.com")

        self.logger.info(f"Set {len(cookies)} Mouser cookies on session")

    def refresh_cookies(self):
        """Force refresh cookies and update session."""
        if self.cookie_manager.refresh_cookies():
            self._set_mouser_cookies()
            self.logger.info("Cookies refreshed successfully")
            return True
        else:
            self.logger.warning("Failed to refresh cookies")
            return False

    def _update_session_cookies(self, response):
        """Update session cookies from response if needed."""
        # This method can be called after each request to maintain session
        if response.cookies:
            for cookie in response.cookies:
                self.session.cookies.set(cookie.name, cookie.value, domain=cookie.domain)
            self.logger.debug("Session cookies updated from response")

    def _make_request(self, url: str, **kwargs) -> requests.Response:
        """
        Override to handle Mouser-specific request processing.
        """
        # Call parent method to get the response
        response = super()._make_request(url, **kwargs)

        # Update session cookies from response
        self._update_session_cookies(response)

        return response

    def scrape_product(self, product_url: str) -> ScrapingResult:
        """
        Scrape product information from Mouser product page.

        Args:
            product_url: URL of the Mouser product page

        Returns:
            ScrapingResult with product information or error details
        """
        start_time = time.time()

        try:
            # Validate URL
            if not self.validate_url(product_url):
                return ScrapingResult(success=False, error_message=f"URL does not belong to {self.vendor_name}")

            # Make request
            response = self._make_request(product_url)
            response_time = (time.time() - start_time) * 1000

            # Parse HTML
            soup = self._parse_html(response.text)

            # Extract product information
            product_info = self.extract_product_info(soup, product_url)

            return ScrapingResult(
                success=True,
                product_info=product_info,
                response_time_ms=response_time,
                http_status_code=response.status_code,
            )

        except Exception as e:
            self.logger.error(f"Error scraping {product_url}: {e}")
            return ScrapingResult(
                success=False, error_message=str(e), response_time_ms=(time.time() - start_time) * 1000
            )

    def extract_product_info(self, soup: BeautifulSoup, url: str) -> ProductInfo:
        """
        Extract product information from parsed HTML.

        Args:
            soup: BeautifulSoup object of the product page
            url: Original URL of the product page

        Returns:
            ProductInfo object with extracted data
        """
        # Extract basic product information
        title = self._extract_title(soup)
        vendor_part_number = self._extract_vendor_part_number(soup)

        # Extract specifications
        specifications = self._extract_specifications(soup)

        # Extract pricing
        pricing = self._extract_pricing(soup)

        # Extract availability
        availability = self._extract_availability(soup)

        # Extract media
        media = self._extract_media(soup, url)

        return ProductInfo(
            vendor_name=self.vendor_name,
            vendor_part_number=vendor_part_number,
            product_url=url,
            title=title,
            specifications=specifications,
            pricing=pricing,
            availability=availability,
            media=media,
            scraper_version="1.0",
        )

    def validate_url(self, url: str) -> bool:
        """
        Validate if the URL belongs to Mouser Electronics.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid for Mouser
        """
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix if present
            if domain.startswith("www."):
                domain = domain[4:]

            # List of Mouser domains
            mouser_domains = [
                "mouser.com",
                "au.mouser.com",
                "uk.mouser.com",
                "de.mouser.com",
                "fr.mouser.com",
                # Add other regional Mouser domains as needed
            ]

            return domain in mouser_domains

        except Exception:
            return False

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract product title."""
        # TODO: Find Mouser's title selectors using browser inspection
        selectors = [
            "span.bc-no-link",
            "span#spnDescription",
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return re.sub(r"\s+", " ", self._extract_text_safe(element).strip())

        return "Unknown Product"

    def _extract_vendor_part_number(self, soup: BeautifulSoup) -> str:
        """Extract Mouser part number."""
        # TODO: Find Mouser's part number selectors
        selectors = [
            "span#spnMouserPartNumFormattedForProdInfo",  # Mouser's product part number heading
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = self._extract_text_safe(element)
                if text:
                    return text.strip()

        return "Unknown"

    def _extract_specifications(self, soup: BeautifulSoup) -> ProductSpecifications:
        """Extract product specifications."""
        specs = ProductSpecifications()

        def cycle_selectors(selectors: List[str]) -> str:
            """Cycle through selectors to find the first matching element."""
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    return re.sub(r"\s+", " ", self._extract_text_safe(element).strip())
            return "Unknown"

        specs.manufacturer = cycle_selectors(["a#lnkManufacturerName", 'a[itemprop="url"]'])
        specs.manufacturer_part_number = cycle_selectors(["span#spnManufacturerPartNumber", "h1.panel-title"])
        specs.description = cycle_selectors(["span#spnDescription", "h1.panel-title"])

        # Breadcrumbs for category and subcategory
        breadcrumbs = soup.select("ol.breadcrumb li a")
        if breadcrumbs:
            if len(breadcrumbs) >= 2:
                specs.category = self._extract_text_safe(breadcrumbs[1])
            if len(breadcrumbs) >= 3:
                specs.subcategory = self._extract_text_safe(breadcrumbs[2])
            else:
                specs.subcategory = "Unknown"

        # Extract technical specifications table
        specs_table = soup.select_one("table.specs-table")
        specs.technical_specs = self._parse_specifications_table(specs_table)

        # TODO: Extract datasheet URL
        # specs.datasheet_url = ...

        # TODO: Extract detailed description
        # specs.detailed_description = ...

        return specs

    def _extract_pricing(self, soup: BeautifulSoup) -> ProductPricing:
        """Extract pricing information."""
        pricing = ProductPricing(currency="AUD")

        stock_and_pricing = soup.select_one("div.pdp-product-availability-pricing")
        if not stock_and_pricing:
            self.logger.warning("No stock and pricing information found")
            return pricing

        price_table = stock_and_pricing.select_one("table")
        if not price_table:
            self.logger.warning("No pricing table found")
            return pricing

        # TODO: Extract main price
        # pricing.unit_price = ...

        # TODO: Extract tax-inclusive price if available
        # pricing.unit_price_inc_tax = ...

        # Extract quantity breaks
        pricing.quantity_breaks = {}
        rows = price_table.select("tr")
        for row in rows:
            if len(row.select("th")) > 1:
                continue
            try:
                qty = int(self._extract_text_safe(row.select_one("th")).strip())
                price = self._extract_text_safe(row.select_one("td")).strip()
                if price:
                    # Convert price to Decimal, handling currency symbols
                    price = re.sub(r"[^\d.]", "", price)
                    pricing.quantity_breaks[qty] = Decimal(price)
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Error parsing quantity break: {e}")
                continue

        if pricing.quantity_breaks:
            # Set the main unit price as the first quantity break
            first_qty = next(iter(pricing.quantity_breaks))
            pricing.package_price = pricing.quantity_breaks[first_qty]
            pricing.minimum_order_quantity = first_qty
            # TODO: Se if this is right - no Mouser multiple unit per packages yet
            pricing.package_quantity = first_qty
        else:
            self.logger.warning("No valid quantity breaks found")

        return pricing

    def _extract_availability(self, soup: BeautifulSoup) -> ProductAvailability:
        """Extract availability information."""
        availability = ProductAvailability()

        # Check stock status
        stock_and_pricing = soup.select_one("div.pdp-product-availability-pricing")

        if not stock_and_pricing:
            self.logger.warning("No stock and pricing information found")
            return availability

        # Extract stock status text
        stock_text = self._extract_text_safe(stock_and_pricing.select_one("div.pdp-product-availability dd div"))
        if stock_text:
            stock_text = stock_text.strip().lower()
            if "can dispatch immediately" in stock_text or "in stock" in stock_text:
                availability.in_stock = True
                availability.lead_time_days = 0
                availability.lead_time_description = stock_text
                # Extract numeric characters from stock_text (e.g., "1,234 In Stock")
                qty_match = re.search(r"[\d,]+", stock_text)
                if qty_match:
                    qty_str = qty_match.group(0).replace(",", "")
                    try:
                        availability.stock_quantity = int(qty_str)
                    except ValueError:
                        availability.stock_quantity = None
                else:
                    availability.stock_quantity = None
            elif "on order" in stock_text or "backorder" in stock_text:
                availability.in_stock = False
                availability.stock_quantity = 0
                availability.lead_time_days = 0  # TODO: Extract lead time if available
                availability.lead_time_description = stock_text
            else:
                availability.in_stock = None
        else:
            self.logger.warning("No stock status found")
            availability.in_stock = None

        return availability

    def _extract_media(self, soup: BeautifulSoup, base_url: str) -> ProductMedia:
        """Extract product images and media."""
        media = ProductMedia()

        img = soup.select_one("img", {"id": "defaultImg"})
        if img and img.has_attr("src"):
            media.primary_image_url = urljoin(base_url, img["src"])

        # TODO: Extract additional images
        # media.additional_images = ...

        return media

    def _parse_specifications_table(self, table_element) -> Dict[str, Any]:
        """Parse technical specifications table."""
        specs: Dict[str, str] = {}

        rows = table_element.select("tr")
        for row in rows:
            if row.select("th"):
                continue  # Skip header rows
            key = self._extract_text_safe(row.select_one("td:nth-of-type(1)")).replace(":", "")
            value = self._extract_text_safe(row.select_one("td:nth-of-type(2)"))
            if key and value:
                specs[key] = value

        return specs


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    scraper = MouserScraper()

    # Test URLs - use the FULL URL with query parameters
    product_urls = [
        "https://au.mouser.com/ProductDetail/Amphenol-RF/242125-10?qs=Z6N%252BYuApFLUnaRyl89ktQw%3D%3D",
        "https://au.mouser.com/ProductDetail/571-DT04-2P-KIT",
    ]

    for product_url in product_urls:
        result = scraper.scrape_product(product_url)

        if result.success:
            print("Product scraped successfully:")
            print(result.product_info)
        else:
            print(f"Error scraping product: {result.error_message}")
