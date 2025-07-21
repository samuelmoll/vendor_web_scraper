# Vendor Web Scraper

A modular, extensible framework for scraping product information from vendor websites with support for multiple output formats including InvenTree import.

## Features

- **Extensible Architecture**: Easy to add new vendor scrapers
- **Multiple Export Formats**: Excel, JSON, InvenTree-compatible formats
- **Rate Limiting**: Built-in delays and retry mechanisms
- **Error Handling**: Robust error handling and logging
- **CLI Interface**: Command-line tool for batch processing
- **Browser Extension Support**: Framework ready for Firefox addon integration

## Supported Vendors

Currently implemented:
- **RS Components** (au.rs-online.com, rs-online.com)

Planned:
- Digikey
- Mouser
- Farnell/Element14
- And more...

## Installation

### Development Installation

```bash
cd vendor-web-scraper
pip install -e .
```

### Requirements

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from vendor_web_scraper import get_scraper, ExcelExporter

# Get scraper for a URL
url = "https://au.rs-online.com/web/p/resistors/7077615"
scraper = get_scraper(url)

# Scrape product information
result = scraper.scrape_product(url)

if result.success:
    product = result.product_info
    print(f"Product: {product.title}")
    print(f"Price: {product.pricing.unit_price} {product.pricing.currency}")
    
    # Export to Excel
    exporter = ExcelExporter()
    df = exporter.export_multiple([product])
    file_path = exporter.save_to_file(df)
    print(f"Exported to: {file_path}")
```

### Command Line Usage

```bash
# Scrape single URL
vendor-scraper scrape https://uk.rs-online.com/web/p/resistors/7077615

# Scrape multiple URLs to Excel
vendor-scraper scrape \\
  https://uk.rs-online.com/web/p/resistors/7077615 \\
  https://uk.rs-online.com/web/p/capacitors/1234567 \\
  --output products.xlsx \\
  --format excel

# Export in InvenTree format
vendor-scraper scrape URL --format inventree --output products.json

# List available scrapers
vendor-scraper list-vendors

# Test URL support
vendor-scraper test-url https://uk.rs-online.com/web/p/resistors/7077615
```

## Architecture

### Core Components

1. **BaseScraper**: Abstract base class for all vendor scrapers
2. **ProductInfo**: Pydantic model for standardized product data
3. **ScraperFactory**: Factory for creating appropriate scrapers
4. **Exporters**: Convert scraped data to various formats

### Data Model

The `ProductInfo` model standardizes product data across vendors:

```python
ProductInfo(
    vendor_name="RS Components",
    vendor_part_number="123-4567",
    title="Example Resistor",
    specifications=ProductSpecifications(
        manufacturer="Vishay",
        category="Resistors",
        description="1kΩ ±1% 0.125W"
    ),
    pricing=ProductPricing(
        currency="AUD",
        unit_price=Decimal("0.15"),
        quantity_breaks={100: Decimal("0.12"), 1000: Decimal("0.10")}
    ),
    availability=ProductAvailability(
        in_stock=True,
        stock_quantity=5000,
        lead_time_days=1
    )
)
```

## Creating New Scrapers

To add support for a new vendor:

1. **Create scraper class**:

```python
from vendor_web_scraper.core.scraper_base import BaseScraper

class NewVendorScraper(BaseScraper):
    def __init__(self, **kwargs):
        super().__init__(
            vendor_name="New Vendor",
            base_url="https://newvendor.com",
            **kwargs
        )
    
    def extract_product_info(self, soup, url):
        # Implement extraction logic
        return ProductInfo(...)
```

2. **Register the scraper**:

```python
from vendor_web_scraper.core.scraper_factory import register_scraper

register_scraper(
    vendor_name="new_vendor",
    scraper_class=NewVendorScraper,
    domains=["newvendor.com", "www.newvendor.com"]
)
```

## Export Formats

### Excel Export

Creates formatted Excel files with:
- Product information table
- Auto-sized columns
- Summary sheet (for multiple products)

### InvenTree Export

Generates JSON compatible with InvenTree import:
- Part information
- Category mapping
- Supplier details
- Pricing data

### Direct InvenTree Integration

```python
from vendor_web_scraper.exporters.inventree_exporter import InvenTreeExporter

exporter = InvenTreeExporter(
    api_url="https://inventree.example.com/api/",
    api_token="your_token_here"
)

# Create parts directly in InvenTree
results = exporter.create_parts_in_inventree(products)
```

## Configuration

### Environment Variables

```bash
# InvenTree integration
INVENTREE_API_URL=https://inventree.example.com/api/
INVENTREE_API_TOKEN=your_token_here

# Scraping settings
SCRAPER_DELAY=1.0
SCRAPER_TIMEOUT=30
SCRAPER_MAX_RETRIES=3
```

### Custom Headers

```python
scraper = get_scraper(url, custom_headers={
    'User-Agent': 'Your Custom User Agent',
    'Accept-Language': 'en-US,en;q=0.9'
})
```

## Firefox Extension

The framework is designed to support a Firefox extension for single-click scraping. The extension structure is prepared in `src/vendor_web_scraper_firefox_addon/`.

## Development

### Project Structure

```
vendor-web-scraper/
├── src/vendor_web_scraper/
│   ├── core/              # Core framework components
│   ├── scrapers/          # Vendor-specific scrapers
│   ├── exporters/         # Export format handlers
│   ├── utils/             # Utility functions
│   └── cli.py             # Command line interface
├── examples/              # Usage examples
├── tests/                 # Test suite
└── pyproject.toml         # Project configuration
```

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Check types
mypy src/

# Lint
flake8 src/ tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your vendor scraper or enhancement
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Roadmap

- [ ] Additional vendor scrapers (Digikey, Mouser, Farnell)
- [ ] Firefox extension implementation
- [ ] Async scraping support
- [ ] Image download and processing
- [ ] Enhanced data validation
- [ ] Web dashboard for monitoring
- [ ] Docker containerization
- [ ] Cloud deployment guides
