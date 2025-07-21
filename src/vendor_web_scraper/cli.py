"""
Command line interface for the vendor web scraper.
"""

import click
import logging
from pathlib import Path
from typing import List

from .core.scraper_factory import get_scraper
from .exporters.excel_exporter import ExcelExporter
from .exporters.inventree_exporter import InvenTreeExporter
from . import scrapers  # Import to trigger scraper registration


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(verbose):
    """Vendor Web Scraper - Extract product data from vendor websites."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@main.command()
@click.argument('urls', nargs=-1, required=True)
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--format', '-f', 
              type=click.Choice(['excel', 'json', 'inventree']),
              default='excel',
              help='Output format')
@click.option('--delay', '-d', type=float, default=1.0, 
              help='Delay between requests (seconds)')
def scrape(urls: List[str], output: str, format: str, delay: float):
    """Scrape product information from URLs."""
    
    click.echo(f"Scraping {len(urls)} URL(s)...")
    
    all_products = []
    
    for url in urls:
        click.echo(f"Processing: {url}")
        
        # Get appropriate scraper
        scraper = get_scraper(url, delay_between_requests=delay)
        
        if not scraper:
            click.echo(f"  ❌ No scraper available for URL: {url}", err=True)
            continue
        
        # Scrape the product
        result = scraper.scrape_product(url)
        
        if result.success:
            click.echo(f"  ✅ Successfully scraped: {result.product_info.title}")
            all_products.append(result.product_info)
        else:
            click.echo(f"  ❌ Failed to scrape: {result.error_message}", err=True)
    
    if not all_products:
        click.echo("No products were successfully scraped.", err=True)
        return
    
    # Export results
    if format == 'excel':
        exporter = ExcelExporter(Path(output).parent if output else None)
        df = exporter.export_multiple(all_products)
        file_path = exporter.save_to_file(df, Path(output).name if output else None)
        click.echo(f"Exported {len(all_products)} products to: {file_path}")
    
    elif format == 'inventree':
        exporter = InvenTreeExporter(Path(output).parent if output else None)
        data = exporter.export_multiple(all_products)
        file_path = exporter.save_to_file(data, Path(output).name if output else None)
        click.echo(f"Exported {len(all_products)} products to: {file_path}")
    
    elif format == 'json':
        import json
        output_path = Path(output) if output else Path('scraped_products.json')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = [product.dict() for product in all_products]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        
        click.echo(f"Exported {len(all_products)} products to: {output_path}")


@main.command()
def list_vendors():
    """List available vendor scrapers."""
    from .core.scraper_factory import factory
    
    vendors = factory.get_available_vendors()
    domains = factory.get_supported_domains()
    
    click.echo("Available vendor scrapers:")
    for vendor in vendors:
        vendor_domains = [d for d, v in domains.items() if v == vendor]
        click.echo(f"  • {vendor}: {', '.join(vendor_domains)}")


@main.command()
@click.argument('url')
def test_url(url: str):
    """Test if a URL is supported by any scraper."""
    from .core.scraper_factory import factory
    
    scraper = get_scraper(url)
    
    if scraper:
        click.echo(f"✅ URL is supported by: {scraper.vendor_name}")
        click.echo(f"   Scraper class: {scraper.__class__.__name__}")
        click.echo(f"   Base URL: {scraper.base_url}")
    else:
        click.echo(f"❌ No scraper available for URL: {url}")
        
        # Show available domains
        domains = factory.get_supported_domains()
        click.echo("\\nSupported domains:")
        for domain in sorted(domains.keys()):
            click.echo(f"  • {domain}")


if __name__ == '__main__':
    main()
