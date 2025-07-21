#!/usr/bin/env python3
"""
Test script for the RS Components scraper.
"""

import sys
import os

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

print(f"Added to Python path: {src_path}")

# Now import our modules
from vendor_web_scraper.core.scraper_factory import get_scraper
from vendor_web_scraper.exporters.excel_exporter import ExcelExporter
from vendor_web_scraper import scrapers  # Import to register scrapers

def test_scraper_registration():
    """Test that scrapers are properly registered."""
    print("Testing scraper registration...")
    
    from vendor_web_scraper.core.scraper_factory import factory
    
    available_vendors = factory.get_available_vendors()
    supported_domains = factory.get_supported_domains()
    
    print(f"Available vendors: {available_vendors}")
    print(f"Supported domains: {supported_domains}")
    
    # Test RS Components URL
    test_url = "https://au.rs-online.com/web/p/resistors/123456"
    scraper = get_scraper(test_url)
    
    if scraper:
        print(f"✅ Scraper found for {test_url}: {scraper.vendor_name}")
        print(f"   Base URL: {scraper.base_url}")
        print(f"   Scraper class: {scraper.__class__.__name__}")
    else:
        print(f"❌ No scraper found for {test_url}")

def test_data_models():
    """Test the data models."""
    print("\nTesting data models...")
    
    from vendor_web_scraper.core.product_model import (
        ProductInfo, ProductSpecifications, ProductPricing, 
        ProductAvailability, ProductMedia
    )
    from decimal import Decimal
    
    # Create test product info
    specs = ProductSpecifications(
        manufacturer="Test Manufacturer",
        manufacturer_part_number="TEST123",
        category="Test Category",
        description="Test description"
    )
    
    pricing = ProductPricing(
        currency="AUD",
        unit_price=Decimal("1.50"),
        quantity_breaks={100: Decimal("1.25"), 1000: Decimal("1.00")},
        minimum_order_quantity=10
    )
    
    availability = ProductAvailability(
        in_stock=True,
        stock_quantity=500,
        lead_time_days=3
    )
    
    media = ProductMedia(
        primary_image_url="https://example.com/image.jpg"
    )
    
    product = ProductInfo(
        vendor_name="Test Vendor",
        vendor_part_number="TV123456",
        product_url="https://example.com/product/123456",
        title="Test Product",
        specifications=specs,
        pricing=pricing,
        availability=availability,
        media=media
    )
    
    print(f"✅ Created test product: {product.title}")
    print(f"   Vendor: {product.vendor_name}")
    print(f"   Price: {product.pricing.unit_price} {product.pricing.currency}")
    print(f"   Manufacturer: {product.specifications.manufacturer}")
    
    # Test export formats
    excel_row = product.to_excel_row()
    inventree_format = product.to_inventree_format()
    
    print(f"✅ Excel export keys: {list(excel_row.keys())[:5]}...")
    print(f"✅ InvenTree export keys: {list(inventree_format.keys())[:5]}...")

def test_exporters():
    """Test the export functionality."""
    print("\nTesting exporters...")
    
    from vendor_web_scraper.exporters.excel_exporter import ExcelExporter
    from vendor_web_scraper.exporters.inventree_exporter import InvenTreeExporter
    
    # Create exporters
    excel_exporter = ExcelExporter()
    inventree_exporter = InvenTreeExporter()
    
    print("✅ Excel exporter created")
    print("✅ InvenTree exporter created")

def test_rs_components_scraper():
    """Test RS Components scraper with sample data."""
    print("\nTesting RS Components scraper...")
    
    from vendor_web_scraper.scrapers.rs_components import RSComponentsScraper
    from bs4 import BeautifulSoup
    
    # Create scraper instance
    scraper = RSComponentsScraper()
    print(f"✅ RS Components scraper created: {scraper.vendor_name}")
    print(f"   Base URL: {scraper.base_url}")
    
    # Test URL validation
    valid_urls = [
        "https://au.rs-online.com/web/p/resistors/123456",
        "https://rs-online.com/web/p/capacitors/789012"
    ]
    
    invalid_urls = [
        "https://digikey.com/product/123456",
        "https://mouser.com/product/789012"
    ]
    
    print("\n   Testing URL validation:")
    for url in valid_urls:
        is_valid = scraper.validate_url(url)
        print(f"   {'✅' if is_valid else '❌'} {url}")
    
    for url in invalid_urls:
        is_valid = scraper.validate_url(url)
        print(f"   {'❌' if not is_valid else '✅'} {url}")
    
    # Test HTML parsing methods with sample HTML
    sample_html = """
    <html>
        <body>
            <h1 data-testid="product-title">Sample Resistor 1kΩ</h1>
            <span data-testid="stock-number">Stock No. 123-4567</span>
            <div data-testid="manufacturer-name">Vishay</div>
            <div data-testid="manufacturer-part-number">CRCW08051K00FKEA</div>
            <div data-testid="product-description">1kΩ ±1% 0.125W 0805 Thick Film Resistor</div>
            <div data-testid="unit-price">AU$0.15</div>
            <div data-testid="stock-status">In Stock - 5000 available</div>
            <img data-testid="product-image" src="//example.com/image.jpg" alt="Product">
        </body>
    </html>
    """
    
    soup = BeautifulSoup(sample_html, 'html.parser')
    
    # Test extraction methods
    title = scraper._extract_title(soup)
    part_number = scraper._extract_part_number(soup)
    specs = scraper._extract_specifications(soup)
    pricing = scraper._extract_pricing(soup)
    availability = scraper._extract_availability(soup)
    media = scraper._extract_media(soup, scraper.base_url)
    
    print(f"\n   Extracted data from sample HTML:")
    print(f"   Title: {title}")
    print(f"   Part Number: {part_number}")
    print(f"   Manufacturer: {specs.manufacturer}")
    print(f"   MPN: {specs.manufacturer_part_number}")
    print(f"   Description: {specs.description}")
    print(f"   Price: {pricing.unit_price} {pricing.currency}")
    print(f"   In Stock: {availability.in_stock}")
    print(f"   Stock Qty: {availability.stock_quantity}")
    print(f"   Image URL: {media.primary_image_url}")

if __name__ == "__main__":
    print("🧪 Running Vendor Web Scraper Tests")
    print("=" * 50)
    
    try:
        test_scraper_registration()
        test_data_models()
        test_exporters()
        test_rs_components_scraper()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
