"""
Example usage of the vendor web scraper.
"""

import logging
from pathlib import Path

# Import the scraper components
from vendor_web_scraper.core.scraper_factory import get_scraper
from vendor_web_scraper.exporters.excel_exporter import ExcelExporter
from vendor_web_scraper.exporters.inventree_exporter import InvenTreeExporter
from vendor_web_scraper import scrapers  # Import to register scrapers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_scrape_single_product():
    """Demonstrate scraping a single product."""
    
    # Example RS Components URL
    url = "https://uk.rs-online.com/web/p/resistors/7077615"
    
    logger.info(f"Scraping product from: {url}")
    
    # Get appropriate scraper for the URL
    scraper = get_scraper(url)
    
    if not scraper:
        logger.error("No scraper available for this URL")
        return
    
    logger.info(f"Using scraper: {scraper.vendor_name}")
    
    # Scrape the product
    result = scraper.scrape_product(url)
    
    if result.success:
        product = result.product_info
        logger.info(f"Successfully scraped: {product.title}")
        logger.info(f"Vendor Part Number: {product.vendor_part_number}")
        logger.info(f"Price: {product.pricing.unit_price} {product.pricing.currency}")
        logger.info(f"Manufacturer: {product.specifications.manufacturer}")
        
        # Export to Excel
        exporter = ExcelExporter()
        df = exporter.export_multiple([product])
        excel_path = exporter.save_to_file(df)
        logger.info(f"Exported to Excel: {excel_path}")
        
        # Export to InvenTree format
        inventree_exporter = InvenTreeExporter()
        inventree_data = inventree_exporter.export_multiple([product])
        json_path = inventree_exporter.save_to_file(inventree_data)
        logger.info(f"Exported to InvenTree format: {json_path}")
        
    else:
        logger.error(f"Failed to scrape: {result.error_message}")


def demo_scrape_multiple_products():
    """Demonstrate scraping multiple products."""
    
    urls = [
        "https://uk.rs-online.com/web/p/resistors/7077615",
        "https://uk.rs-online.com/web/p/capacitors/1234567",  # This might fail
        # Add more URLs here
    ]
    
    logger.info(f"Scraping {len(urls)} products...")
    
    all_products = []
    
    for url in urls:
        logger.info(f"Processing: {url}")
        
        scraper = get_scraper(url)
        if not scraper:
            logger.warning(f"No scraper for URL: {url}")
            continue
        
        result = scraper.scrape_product(url)
        
        if result.success:
            logger.info(f"✅ {result.product_info.title}")
            all_products.append(result.product_info)
        else:
            logger.error(f"❌ {result.error_message}")
    
    if all_products:
        # Export all products to Excel
        exporter = ExcelExporter()
        df = exporter.export_multiple(all_products)
        excel_path = exporter.save_to_file(df, "multiple_products.xlsx")
        logger.info(f"Exported {len(all_products)} products to: {excel_path}")


def demo_list_available_scrapers():
    """Show available scrapers and supported domains."""
    
    from vendor_web_scraper.core.scraper_factory import factory
    
    vendors = factory.get_available_vendors()
    domains = factory.get_supported_domains()
    
    logger.info("Available scrapers:")
    for vendor in vendors:
        vendor_domains = [d for d, v in domains.items() if v == vendor]
        logger.info(f"  • {vendor}: {', '.join(vendor_domains)}")


def demo_test_url_support():
    """Test if various URLs are supported."""
    
    test_urls = [
        "https://uk.rs-online.com/web/p/resistors/7077615",
        "https://www.digikey.com/product-detail/en/yageo/RC0603FR-071KL/311-1.0KHRCT-ND/729790",
        "https://www.mouser.com/ProductDetail/71-CRCW08051K00FKEA",
        "https://uk.farnell.com/vishay/crcw08051k00fkea/res-1k-1-0-125w-0805-thick-film/dp/2447553"
    ]
    
    logger.info("Testing URL support:")
    
    for url in test_urls:
        scraper = get_scraper(url)
        if scraper:
            logger.info(f"✅ {url} -> {scraper.vendor_name}")
        else:
            logger.info(f"❌ {url} -> No scraper available")


if __name__ == "__main__":
    print("Vendor Web Scraper Demo")
    print("=" * 50)
    
    # Demo 1: List available scrapers
    print("\\n1. Available Scrapers:")
    demo_list_available_scrapers()
    
    # Demo 2: Test URL support
    print("\\n2. URL Support Test:")
    demo_test_url_support()
    
    # Demo 3: Scrape single product (uncomment to test with real URL)
    # print("\\n3. Single Product Scraping:")
    # demo_scrape_single_product()
    
    # Demo 4: Scrape multiple products (uncomment to test)
    # print("\\n4. Multiple Product Scraping:")
    # demo_scrape_multiple_products()
    
    print("\\nDemo completed!")
