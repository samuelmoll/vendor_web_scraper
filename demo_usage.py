#!/usr/bin/env python3
"""
Simple demo script showing how to use the vendor web scraper.
"""

import sys
import os

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), "src")
sys.path.insert(0, src_path)

from vendor_web_scraper.core.scraper_factory import get_scraper
from vendor_web_scraper.exporters.excel_exporter import ExcelExporter
from vendor_web_scraper.exporters.inventree_exporter import InvenTreeExporter
from vendor_web_scraper import scrapers  # Import to register scrapers


def demo_scraper_usage():
    """Demonstrate basic scraper usage."""

    print("🔧 Vendor Web Scraper Demo")
    print("=" * 40)

    # Example URLs (these are fake for demo purposes)
    test_urls = [
        "https://uk.rs-online.com/web/p/resistors/123456",
        "https://au.rs-online.com/web/p/capacitors/789012",
        "https://sg.rs-online.com/web/p/inductors/345678",
    ]

    print("\\n1. Testing URL Support:")
    for url in test_urls:
        scraper = get_scraper(url)
        if scraper:
            print(f"   ✅ {url}")
            print(f"      -> {scraper.vendor_name} ({scraper.__class__.__name__})")
        else:
            print(f"   ❌ {url} - No scraper available")

    print("\\n2. Available Scrapers:")
    from vendor_web_scraper.core.scraper_factory import factory

    vendors = factory.get_available_vendors()
    domains = factory.get_supported_domains()

    for vendor in vendors:
        vendor_domains = [d for d, v in domains.items() if v == vendor]
        print(f"   • {vendor}:")
        for domain in sorted(vendor_domains):
            print(f"     - {domain}")

    print(f"\\n   Total: {len(vendors)} vendor(s), {len(domains)} domain(s)")

    print("\\n3. Sample Scraping Process:")

    # Get a scraper instance
    url = "https://uk.rs-online.com/web/p/resistors/123456"
    scraper = get_scraper(url)

    if scraper:
        print(f"   📋 Selected scraper: {scraper.vendor_name}")
        print(f"   🌐 Base URL: {scraper.base_url}")
        print(f"   🔍 Validates URL: {scraper.validate_url(url)}")
        print(f"   ⚙️  Rate limit: {scraper.delay_between_requests}s between requests")
        print(f"   🔄 Max retries: {scraper.max_retries}")
        print(f"   ⏱️  Timeout: {scraper.timeout}s")

        print("\\n   📝 To scrape a real product:")
        print("      result = scraper.scrape_product(product_url)")
        print("      if result.success:")
        print("          product = result.product_info")
        print("          # Export to Excel")
        print("          exporter = ExcelExporter()")
        print("          df = exporter.export_multiple([product])")
        print("          file_path = exporter.save_to_file(df)")

    print("\\n4. Export Options:")
    print("   📊 Excel Export:")
    print("      - Formatted spreadsheets with auto-sizing")
    print("      - Summary sheets for multiple products")
    print("      - Compatible with Excel, LibreOffice, Google Sheets")

    print("\\n   🔗 InvenTree Export:")
    print("      - JSON format compatible with InvenTree import")
    print("      - Direct API integration (with credentials)")
    print("      - Auto-creates missing categories and suppliers")

    print("\\n5. Command Line Usage:")
    print("   vendor-scraper scrape URL1 URL2 --output products.xlsx")
    print("   vendor-scraper list-vendors")
    print("   vendor-scraper test-url https://uk.rs-online.com/web/p/123456")

    print("\\n" + "=" * 40)
    print("🚀 Ready to scrape! Provide RS Components HTML source for customization.")


if __name__ == "__main__":
    demo_scraper_usage()
