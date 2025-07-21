"""
Scraper registry initialization and configuration.
"""

from ..core.scraper_factory import register_scraper
from .rs_components import RSComponentsScraper


def register_all_scrapers():
    """Register all available scrapers with the factory."""
    
    # RS Components
    register_scraper(
        vendor_name="rs_components",
        scraper_class=RSComponentsScraper,
        domains=[
            "uk.rs-online.com",
            "rs-online.com",
            "au.rs-online.com",
            "sg.rs-online.com",
            "export.rs-online.com",
            "ie.rs-online.com",
            "fr.rs-online.com",
            "de.rs-online.com"
        ]
    )
    
    # Add more scrapers here as they're implemented
    # register_scraper("digikey", DigikeyScaper, ["digikey.com", "digikey.co.uk"])
    # register_scraper("mouser", MouserScraper, ["mouser.com", "mouser.co.uk"])
    # register_scraper("farnell", FarnellScraper, ["farnell.com", "element14.com"])


# Auto-register scrapers when module is imported
register_all_scrapers()
