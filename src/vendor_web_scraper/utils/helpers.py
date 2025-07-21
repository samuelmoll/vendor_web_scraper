"""
Utility functions for the vendor web scraper.
"""

import re
import time
import random
from typing import List, Optional
from urllib.parse import urlparse, urljoin


def clean_text(text: str) -> str:
    """
    Clean and normalize text content.

    Args:
        text: Raw text to clean

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove leading/trailing whitespace
    text = text.strip()

    # Remove common unwanted characters
    text = re.sub(r"[^\w\s\-\.\,\:\;\(\)\[\]\&\%\$\£\€]", "", text)

    return text


def extract_price_from_text(text: str, currency_symbols: List[str] = None) -> Optional[float]:
    """
    Extract price value from text containing currency information.

    Args:
        text: Text potentially containing price
        currency_symbols: List of currency symbols to look for

    Returns:
        Price value as float or None if not found
    """
    if not text:
        return None

    if currency_symbols is None:
        currency_symbols = ["£", "$", "€", "¥", "USD", "GBP", "EUR", "AUD"]

    # Remove currency symbols and common separators
    cleaned = text.replace(",", "")
    for symbol in currency_symbols:
        cleaned = cleaned.replace(symbol, "")

    # Find decimal number
    price_match = re.search(r"(\d+\.?\d*)", cleaned)

    if price_match:
        try:
            return float(price_match.group(1))
        except ValueError:
            pass

    return None


def extract_quantity_from_text(text: str) -> Optional[int]:
    """
    Extract quantity/stock number from text.

    Args:
        text: Text potentially containing quantity

    Returns:
        Quantity as integer or None if not found
    """
    if not text:
        return None

    # Look for patterns like "5 in stock", "Available: 10", etc.
    qty_patterns = [
        r"(\d+)\s*(?:in stock|available|pieces?|units?)",
        r"(?:stock|available|qty):\s*(\d+)",
        r"(\d+)\s*(?:pcs?|pc|units?)",
    ]

    text_lower = text.lower()

    for pattern in qty_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue

    return None


def normalize_url(url: str, base_url: str = None) -> str:
    """
    Normalize and complete URL.

    Args:
        url: URL to normalize
        base_url: Base URL for relative URLs

    Returns:
        Normalized complete URL
    """
    if not url:
        return ""

    # Handle protocol-relative URLs
    if url.startswith("//"):
        return "https:" + url

    # Handle relative URLs
    if not url.startswith(("http://", "https://")):
        if base_url:
            return urljoin(base_url, url)
        else:
            return "https://" + url.lstrip("/")

    return url


def get_domain_from_url(url: str) -> str:
    """
    Extract domain from URL.

    Args:
        url: URL to extract domain from

    Returns:
        Domain name
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www prefix
        if domain.startswith("www."):
            domain = domain[4:]

        return domain
    except:
        return ""


def random_delay(min_seconds: float = 0.5, max_seconds: float = 2.0) -> None:
    """
    Add random delay to avoid being detected as a bot.

    Args:
        min_seconds: Minimum delay
        max_seconds: Maximum delay
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def validate_part_number(part_number: str) -> bool:
    """
    Validate if a string looks like a valid part number.

    Args:
        part_number: Part number to validate

    Returns:
        True if it looks like a valid part number
    """
    if not part_number or len(part_number) < 3:
        return False

    # Part numbers typically contain alphanumeric characters and some symbols
    if not re.match(r"^[A-Za-z0-9\-_\.]+$", part_number):
        return False

    # Should contain at least one letter or number
    if not re.search(r"[A-Za-z0-9]", part_number):
        return False

    return True


def format_currency(amount: float, currency: str = "AUD") -> str:
    """
    Format currency amount with appropriate symbol.

    Args:
        amount: Amount to format
        currency: Currency code

    Returns:
        Formatted currency string
    """
    symbols = {"AUD": "A$", "GBP": "£", "USD": "$", "EUR": "€", "JPY": "¥"}

    symbol = symbols.get(currency.upper(), currency)
    return f"{symbol}{amount:.2f}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix
