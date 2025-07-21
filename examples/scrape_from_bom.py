import os
import sys
from pathlib import Path
import pandas as pd
import re
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import pickle


try:
    from vendor_web_scraper.core.scraper_factory import get_scraper
    from vendor_web_scraper.exporters.excel_exporter import ExcelExporter
    from vendor_web_scraper.exporters.inventree_exporter import InvenTreeExporter
    from vendor_web_scraper import scrapers  # Import to register scrapers
except ImportError as e:
    print(f"Error importing vendor_web_scraper modules: {e}")
    src_path = Path(__file__).resolve().parent.parent / Path("src")
    print(f"Adding directory {src_path} to Python path: ", end="")
    sys.path.insert(0, str(src_path))
    print(sys.path)

    from vendor_web_scraper.exporters.excel_exporter import ExcelExporter
    from vendor_web_scraper.exporters.inventree_exporter import InvenTreeExporter
    from vendor_web_scraper.core.scraper_factory import get_scraper
    from vendor_web_scraper import scrapers  # Import to register scrapers

BOM_FILE = (
    Path(
        r"C:\Users\samue\Sime Darby Holdings Berhad\Decoda Systems Engineering Team - Documents\CCM\CCM Engineering Documentation\Production Release V3.5\Manufacture and Assembly"
    )
    / "BOM_v3.5.1.xlsx"
)
sheet = "BOM by Assembly"
col = 13

mp.set_start_method("spawn", force=True)


def extract_url(comment: str) -> str:
    """
    Extract a URL from a comment string.

    Args:
        comment: The comment string containing a URL.

    Returns:
        The extracted URL or an empty string if no URL is found.
    """
    try:
        match = re.search(r"(https?://[^\s]+)", comment)
        return match.group(0) if match else ""
    except Exception as e:
        print(f"Error extracting URL from comment: {e}")
        return ""


def scrape_url(url: str, delay: float = 1.0) -> Optional[Dict[str, Any]]:
    """
    Scrape product information from a URL.

    Args:
        url: The URL to scrape.
        delay: Delay between requests in seconds.

    Returns:
        A dictionary with product information or None if scraping fails.
    """
    scraper = get_scraper(url, delay_between_requests=delay)

    if not scraper:
        print(f"❌ No scraper available for URL: {url}")
        return None

    result = scraper.scrape_product(url)

    if result.success:
        return result.product_info
    else:
        print(f"❌ Failed to scrape {url}: {result.error_message}")
        return None


product_info = []

# Use ThreadPoolExecutor to scrape URLs concurrently
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = []
    with open(BOM_FILE, "rb") as f:
        df = pd.read_excel(f, sheet_name=sheet)
        for comment in df.iloc[:, col - 1].dropna():
            url = extract_url(comment)
            if url and "rs-online" in url:
                futures.append(executor.submit(scrape_url, url))

    for future in futures:
        info = future.result()
        if info:
            product_info.append(info)

pickle_file = Path(__file__).parent / "data/scraped_products.pkl"

for product in product_info:
    print(f"Product: {product.get('title', 'N/A')}")
    print(f"Vendor Part Number: {product.get('vendor_part_number', 'N/A')}")
    print(
        f"Price: {product.get('pricing', {}).get('unit_price', 'N/A')} {product.get('pricing', {}).get('currency', 'N/A')}"
    )
    print(f"Manufacturer: {product.get('specifications', {}).get('manufacturer', 'N/A')}")
    print("-" * 40)
