#!/usr/bin/env python3
"""
Development setup script for vendor-web-scraper.

This script sets up the package for development use without requiring
the complex pyproject.toml build system.
"""

import os
import sys
import subprocess
from pathlib import Path


def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")

    # Core dependencies
    dependencies = [
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "lxml>=4.9.0",
        "pandas>=1.5.0",
        "pydantic>=1.10.0",
        "selenium>=4.8.0",
        "fake-useragent>=1.2.0",
        "python-dotenv>=1.0.0",
        "click>=8.1.0",
        "openpyxl>=3.1.0",
        "aiohttp>=3.8.0",
        "asyncio-throttle>=1.0.0",
    ]

    # Optional dependencies
    optional_deps = [
        "inventree>=0.11.0",  # For InvenTree integration
    ]

    for dep in dependencies:
        print(f"  Installing {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to install {dep}: {e}")
            return False

    print("  📦 Core dependencies installed!")

    # Try to install optional dependencies
    print("  📦 Installing optional dependencies...")
    for dep in optional_deps:
        print(f"    Installing {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"    ✅ {dep} installed")
        except subprocess.CalledProcessError:
            print(f"    ⚠️  {dep} failed (optional - continuing)")

    return True


def setup_development_environment():
    """Set up the development environment."""
    print("🔧 Setting up development environment...")

    # Get the project root
    project_root = Path(__file__).parent
    src_path = project_root / "src"

    print(f"  Project root: {project_root}")
    print(f"  Source path: {src_path}")

    # Create a .pth file to add our src directory to Python path
    try:
        import site

        site_packages = site.getsitepackages()[0]
        pth_file = Path(site_packages) / "vendor-web-scraper-dev.pth"

        with open(pth_file, "w", encoding="utf-8") as f:
            f.write(str(src_path.absolute()) + "\n")

        print(f"  ✅ Created .pth file: {pth_file}")
        print(f"     Added path: {src_path.absolute()}")

    except Exception as e:
        print(f"  ❌ Failed to create .pth file: {e}")
        print("  💡 Alternative: Add this to your scripts:")
        print(f"     import sys; sys.path.insert(0, r'{src_path.absolute()}')")
        return False

    return True


def create_cli_script():
    """Create a command-line script."""
    print("⚡ Creating CLI script...")

    project_root = Path(__file__).parent
    src_path = project_root / "src"

    # Create a standalone CLI script
    cli_script = project_root / "vendor_scraper_cli.py"

    cli_content = f'''#!/usr/bin/env python3
"""
Standalone CLI script for vendor-web-scraper.
"""

import sys
import os

# Add src to path
sys.path.insert(0, r"{src_path.absolute()}")

# Import and run CLI
try:
    from vendor_web_scraper.cli import main

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"Import error: {{e}}")
    print("Make sure you've run the setup script first")
    sys.exit(1)
'''

    with open(cli_script, "w", encoding="utf-8") as f:
        f.write(cli_content)

    print(f"  ✅ Created CLI script: {cli_script}")
    print(f"  💡 Usage: python {cli_script.name} --help")

    return True


def test_installation():
    """Test the installation."""
    print("🧪 Testing installation...")

    try:
        # Test basic import
        import vendor_web_scraper

        print("  ✅ Base package import successful")

        # Test factory import
        from vendor_web_scraper.core.scraper_factory import get_scraper

        print("  ✅ Factory import successful")

        # Test scraper registration
        from vendor_web_scraper import scrapers

        print("  ✅ Scrapers imported and registered")

        # Test getting a scraper
        scraper = get_scraper("https://uk.rs-online.com/web/p/test/123456")
        if scraper:
            print(f"  ✅ Scraper found: {scraper.vendor_name}")
        else:
            print("  ❌ No scraper found for test URL")
            return False

        # Test exporters
        from vendor_web_scraper.exporters.excel_exporter import ExcelExporter
        from vendor_web_scraper.exporters.inventree_exporter import InvenTreeExporter

        print("  ✅ Exporters import successful")

        return True

    except ImportError as e:
        print(f"  ❌ Import test failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 Vendor Web Scraper - Development Setup")
    print("=" * 50)
    print("Setting up for internal development use...")
    print()

    # Step 1: Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        return False

    print()

    # Step 2: Setup development environment
    if not setup_development_environment():
        print("❌ Development environment setup failed")
        return False

    print()

    # Step 3: Create CLI script
    if not create_cli_script():
        print("❌ CLI script creation failed")
        return False

    print()

    # Step 4: Test installation
    if not test_installation():
        print("❌ Installation test failed")
        return False

    print()
    print("=" * 50)
    print("✅ Development setup completed successfully!")
    print()
    print("📝 Usage:")
    print("  • Import in Python: from vendor_web_scraper import get_scraper")
    print("  • CLI usage: python vendor_scraper_cli.py --help")
    print("  • Run tests: python test_framework.py")
    print("  • Run demo: python demo_usage.py")
    print()
    print("🔧 Development Notes:")
    print("  • Package is installed in development mode")
    print("  • Changes to source code are immediately available")
    print("  • No need to reinstall after code changes")
    print("  • Use your favorite IDE/editor on the src/ directory")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
