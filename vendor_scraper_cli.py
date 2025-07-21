#!/usr/bin/env python3
"""
Standalone CLI script for vendor-web-scraper.
"""

import sys
import os

# Add src to path
sys.path.insert(0, r"C:\Users\samue\detect-platform\vendor_web_scraper\src")

# Import and run CLI
try:
    from vendor_web_scraper.cli import main

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you've run the setup script first")
    sys.exit(1)
