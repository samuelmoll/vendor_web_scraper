"""
RS Components scraper implementation.
"""

import re
import time
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup

try:
    from ..core.scraper_base import BaseScraper, ScrapingResult
    from ..core.product_model import (
        ProductInfo,
        ProductSpecifications,
        ProductPricing,
        ProductAvailability,
        ProductMedia,
    )
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


class RSComponentsScraper(BaseScraper):
    """
    Scraper for RS Components (rs-online.com) product pages.

    Extracts product information including specifications, pricing,
    availability, and technical details from RS Components product pages.
    """

    def __init__(self, **kwargs):
        """Initialize RS Components scraper."""
        super().__init__(
            vendor_name="RS Components", base_url="https://au.rs-online.com", **kwargs  # Default to AU site
        )

    def scrape_product(self, product_url: str) -> ScrapingResult:
        """
        Scrape product information from RS Components product page.

        Args:
            product_url: URL of the RS Components product page

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
        vendor_part_number = self._extract_part_number(soup)

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
        Validate if the URL belongs to RS Components.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid for RS Components
        """
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix if present
            if domain.startswith("www."):
                domain = domain[4:]

            # List of RS Components domains
            rs_domains = [
                "rs-online.com",
                "uk.rs-online.com",
                "au.rs-online.com",
                "sg.rs-online.com",
                "export.rs-online.com",
                "ie.rs-online.com",
                "fr.rs-online.com",
                "de.rs-online.com",
            ]

            return domain in rs_domains

        except Exception:
            return False

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract product title."""
        # Try multiple selectors for the title
        selectors = [
            'h1[data-testid="product-title"]',
            "h1.product-title",
            "h1",
            ".pdp-product-name h1",
            '[data-qa="product-name"]',
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return self._extract_text_safe(element).strip()

        return "Unknown Product"

    def _extract_part_number(self, soup: BeautifulSoup) -> str:
        """Extract RS part number."""
        # Look for manufacturer part number (Mfr. Part No.)
        selectors = [
            '[data-testid="manufacturer-part-number"]',
            ".mpn",
            '[data-qa="manufacturer-part-number"]',
            'span:-soup-contains("Mfr. Part No.")',
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = self._extract_text_safe(element)
                # Extract part number after "Mfr. Part No.:"
                match = re.search(r"Mfr\. Part No\.:\s*([^\s]+)", text)
                if match:
                    return match.group(1)
                # Fallback: if text is just the part number
                if text and "Mfr. Part No." not in text:
                    return text.strip()

        # Fallback: try to extract from specifications table
        specs_table = soup.select_one('.specifications-table, .tech-specs, [data-testid="specifications"]')
        if specs_table:
            for row in specs_table.find_all("tr"):
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    key = self._extract_text_safe(cells[0]).strip().lower()
                    if "mfr. part no" in key or "manufacturer part number" in key:
                        value = self._extract_text_safe(cells[1]).strip()
                        if value:
                            return value

        return "Unknown"

    def _extract_specifications(self, soup: BeautifulSoup) -> ProductSpecifications:
        """Extract product specifications."""
        specs = ProductSpecifications()

        # Extract manufacturer
        manufacturer_selectors = ['[data-testid="manufacturer-name"]', ".manufacturer-name", '[data-qa="brand-name"]']

        for selector in manufacturer_selectors:
            element = soup.select_one(selector)
            if element:
                specs.manufacturer = self._extract_text_safe(element)
                break

        # Extract manufacturer part number
        mpn_selectors = ['[data-testid="manufacturer-part-number"]', ".mpn", '[data-qa="manufacturer-part-number"]']

        for selector in mpn_selectors:
            element = soup.select_one(selector)
            if element:
                specs.manufacturer_part_number = self._extract_text_safe(element)
                break

        # Extract description
        desc_selectors = ['[data-testid="product-description"]', ".product-description", ".pdp-product-description"]

        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                specs.description = self._extract_text_safe(element)
                break

        # Extract category
        breadcrumb = soup.select_one('.breadcrumb, .breadcrumbs, [data-testid="breadcrumb"]')
        if breadcrumb:
            breadcrumb_items = breadcrumb.find_all("a")
            if len(breadcrumb_items) > 1:
                specs.category = self._extract_text_safe(breadcrumb_items[-2])

        # Extract technical specifications table
        specs_table = soup.select_one('.specifications-table, .tech-specs, [data-testid="specifications"]')
        if specs_table:
            specs.technical_specs = self._parse_specifications_table(specs_table)

        return specs

    def _extract_pricing(self, soup: BeautifulSoup) -> ProductPricing:
        """Extract pricing information."""
        pricing = ProductPricing(currency="AUD")

        # Extract main price
        price_selectors = ['[data-testid="exc-vat"]', ".price-current", ".unit-price", '[data-qa="unit-price"]']

        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = self._extract_text_safe(element)
                price_value = self._extract_number_from_text(price_text)
                if price_value:
                    pricing.unit_price = Decimal(str(price_value))
                break

        element = soup.select_one('[data-testid="inc-vat"]')
        if element:
            price_text = self._extract_text_safe(element)
            price_value = self._extract_number_from_text(price_text)
            if price_value:
                pricing.unit_price_inc_tax = Decimal(str(price_value))

        # Extract quantity breaks
        qty_breaks = {}
        price_breaks_table = soup.select_one('.price-breaks, .quantity-pricing, [data-testid="price-breaks"]')

        if price_breaks_table:
            rows = price_breaks_table.find_all("tr")[1:]  # Skip header
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    qty_text = self._extract_text_safe(cells[0])
                    price_text = self._extract_text_safe(cells[1])

                    qty = self._extract_number_from_text(qty_text)
                    price = self._extract_number_from_text(price_text)

                    if qty and price:
                        qty_breaks[int(qty)] = Decimal(str(price))

        pricing.quantity_breaks = qty_breaks

        # Extract MOQ
        moq_selectors = [
            '[data-testid="price-heading"]',
            '[data-testid="minimum-order-quantity"]',
            ".moq",
            '[data-qa="moq"]',
        ]

        for selector in moq_selectors:
            element = soup.select_one(selector)
            if element:
                moq_text = self._extract_text_safe(element)
                moq_value = self._extract_number_from_text(moq_text)
                if moq_value:
                    pricing.minimum_order_quantity = int(moq_value)
                break

        return pricing

    def _extract_availability(self, soup: BeautifulSoup) -> ProductAvailability:
        """Extract availability information."""
        availability = ProductAvailability()

        # Check stock status
        stock_selectors = [
            '[data-testid="stock-status"]',
            '[data-testid="stock-status-0"]',
            ".stock-status",
            '[data-qa="availability"]',
        ]

        for selector in stock_selectors:
            element = soup.select_one(selector)
            if element:
                stock_text = self._extract_text_safe(element).lower()
                availability.in_stock = "in global stock" in stock_text or "in local stock" in stock_text

                # Extract stock quantity if mentioned
                qty_match = re.search(r"(\d+)\s*(?:in global stock|in local stock)", stock_text)
                if qty_match:
                    availability.stock_quantity = int(qty_match.group(1))
                availability.lead_time_description = stock_text

                # Extract days from text like "5-7 working days"
                days_match = re.search(r"(\d+)(?:-\d+)?\s*(?:working\s*)?day(s)?", stock_text)
                if days_match:
                    availability.lead_time_days = int(days_match.group(1))
                break

        return availability

    def _extract_media(self, soup: BeautifulSoup, base_url: str) -> ProductMedia:
        """Extract product images and media."""
        media = ProductMedia()

        # Extract primary image
        img_selectors = [
            '[data-testid="gallery-fallback-image"]',
            ".product-image img",
            ".pdp-image img",
            ".hero-image img",
        ]

        for selector in img_selectors:
            element = soup.select_one(selector)
            if element and element.get("src"):
                img_url = str(element["src"])
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif img_url.startswith("/"):
                    img_url = urljoin(base_url, img_url)

                media.primary_image_url = str(img_url)
                media.additional_images.extend(str(element["srcset"]).split(", "))
                break

        return media

    def _parse_specifications_table(self, table_element) -> Dict[str, Any]:
        """Parse technical specifications table."""
        specs = {}

        rows = table_element.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                key = self._extract_text_safe(cells[0]).strip()
                value = self._extract_text_safe(cells[1]).strip()

                if key and value:
                    specs[key] = value

        return specs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = RSComponentsScraper()

    # Amphenol Pressure-relief Vent
    product_url = r"https://au.rs-online.com/web/p/enclosure-ventilation/1749400"
    result = scraper.scrape_product(product_url)

    if result.success:
        print("Product scraped successfully:")
        print(result.product_info)
    else:
        print(f"Error scraping product: {result.error_message}")
