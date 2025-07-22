"""
Cookie management utilities for web scrapers.

Provides automated cookie harvesting using Selenium and cookie persistence
for sites with heavy bot detection like Mouser Electronics.
"""

import json
import time
import logging
from typing import Dict, Optional, List
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class CookieManager:
    """
    Manages cookies for web scrapers with automatic harvesting and persistence.
    """

    def __init__(
        self,
        vendor_name: str,
        base_url: str,
        cookie_file: Optional[str] = None,
        cookie_expiry_hours: int = 12,
        auto_refresh: bool = True,
    ):
        """
        Initialize cookie manager.

        Args:
            vendor_name: Name of the vendor (e.g., "Mouser")
            base_url: Base URL of the vendor website
            cookie_file: Path to cookie storage file
            cookie_expiry_hours: Hours before cookies expire
            auto_refresh: Whether to auto-refresh expired cookies
        """
        self.vendor_name = vendor_name
        self.base_url = base_url
        self.cookie_expiry_hours = cookie_expiry_hours
        self.auto_refresh = auto_refresh

        # Set up logging
        self.logger = logging.getLogger(f"{__name__}.{vendor_name}")

        # Cookie file setup
        if cookie_file is None:
            cookie_file = f"{vendor_name.lower()}_cookies.json"
        self.cookie_file = Path(cookie_file)

        # Current cookies
        self.cookies: Dict[str, str] = {}

    def get_valid_cookies(self, fallback_cookies: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Get valid cookies, refreshing if necessary.

        Args:
            fallback_cookies: Hardcoded cookies to use if harvesting fails

        Returns:
            Dictionary of valid cookies
        """
        # Try to load existing cookies
        if self._load_cookies_from_file():
            self.logger.info(f"Using cached cookies for {self.vendor_name}")
            return self.cookies

        # If auto-refresh is enabled, try to harvest fresh cookies
        if self.auto_refresh and SELENIUM_AVAILABLE:
            if self._harvest_fresh_cookies():
                self.logger.info(f"Using fresh harvested cookies for {self.vendor_name}")
                return self.cookies

        # Fall back to provided cookies
        if fallback_cookies:
            self.logger.warning(f"Using fallback cookies for {self.vendor_name}")
            self.cookies = fallback_cookies
            return self.cookies

        # No cookies available
        self.logger.error(f"No valid cookies available for {self.vendor_name}")
        return {}

    def _load_cookies_from_file(self) -> bool:
        """Load cookies from file if they're still valid."""
        try:
            if not self.cookie_file.exists():
                return False

            with open(self.cookie_file, "r") as f:
                cookie_data = json.load(f)

            # Check if cookies are still valid
            expires_at = cookie_data.get("expires_at", 0)
            if time.time() > expires_at:
                self.logger.info(f"Stored cookies for {self.vendor_name} have expired")
                return False

            self.cookies = cookie_data["cookies"]
            self.logger.info(f"Loaded {len(self.cookies)} cookies for {self.vendor_name} from file")
            return True

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            self.logger.warning(f"Error loading cookie file: {e}")
            return False

    def _save_cookies_to_file(self, cookies: Dict[str, str]) -> bool:
        """Save cookies to file with timestamp."""
        try:
            cookie_data = {
                "vendor": self.vendor_name,
                "base_url": self.base_url,
                "cookies": cookies,
                "timestamp": time.time(),
                "expires_at": time.time() + (self.cookie_expiry_hours * 60 * 60),
            }

            # Ensure directory exists
            self.cookie_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.cookie_file, "w") as f:
                json.dump(cookie_data, f, indent=2)

            self.logger.info(f"Cookies saved to {self.cookie_file}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving cookies: {e}")
            return False

    def _harvest_fresh_cookies(self) -> bool:
        """Use Selenium to harvest fresh cookies."""
        if not SELENIUM_AVAILABLE:
            self.logger.error("Selenium not available for cookie harvesting")
            return False

        self.logger.info(f"Harvesting fresh cookies for {self.vendor_name}...")

        driver = None
        try:
            # Setup Chrome options for realistic browsing
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # Add some realistic browser settings
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")  # Only if the site works without JS

            driver = webdriver.Chrome(options=chrome_options)

            # Hide automation indicators
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Navigate to the homepage first
            self.logger.debug(f"Navigating to {self.base_url}")
            driver.get(self.base_url)

            # Wait for page to load
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # Handle cookie consent banners
            self._handle_cookie_consent(driver)

            # Navigate to a product page to trigger more cookies (vendor-specific)
            product_url = self._get_sample_product_url()
            if product_url:
                self.logger.debug(f"Navigating to sample product: {product_url}")
                driver.get(product_url)
                time.sleep(3)

            # Extract cookies
            selenium_cookies = driver.get_cookies()

            # Convert to our format
            fresh_cookies = {}
            for cookie in selenium_cookies:
                fresh_cookies[cookie["name"]] = cookie["value"]

            if fresh_cookies:
                self.cookies = fresh_cookies
                self._save_cookies_to_file(fresh_cookies)
                self.logger.info(f"Successfully harvested {len(fresh_cookies)} cookies")
                return True
            else:
                self.logger.warning("No cookies were harvested")
                return False

        except Exception as e:
            self.logger.error(f"Error harvesting cookies: {e}")
            return False
        finally:
            if driver:
                driver.quit()

    def _handle_cookie_consent(self, driver):
        """Handle cookie consent banners (vendor-specific)."""
        consent_selectors = [
            "#onetrust-accept-btn-handler",  # OneTrust
            "[data-testid='cookie-accept']",
            ".cookie-accept",
            "#cookie-accept",
            "button[title*='Accept']",
            "button[aria-label*='Accept']",
        ]

        for selector in consent_selectors:
            try:
                accept_button = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                accept_button.click()
                self.logger.debug(f"Clicked cookie consent button: {selector}")
                time.sleep(2)
                break
            except:
                logging.warning(f"Cookie consent button not found: {selector}")
                continue

    def _get_sample_product_url(self) -> Optional[str]:
        """Get a sample product URL for the vendor (override in subclasses)."""
        # This should be overridden for specific vendors
        return None

    def refresh_cookies(self) -> bool:
        """Force refresh cookies."""
        return self._harvest_fresh_cookies()

    def clear_cookies(self):
        """Clear stored cookies."""
        self.cookies = {}
        if self.cookie_file.exists():
            self.cookie_file.unlink()
        self.logger.info(f"Cookies cleared for {self.vendor_name}")


class MouserCookieManager(CookieManager):
    """Specialized cookie manager for Mouser Electronics."""

    def __init__(self, **kwargs):
        super().__init__(vendor_name="Mouser", base_url="https://au.mouser.com", **kwargs)

    def _get_sample_product_url(self) -> str:
        """Get a sample Mouser product URL."""
        return "https://au.mouser.com/ProductDetail/Amphenol-RF/242125-10?qs=sGAEpiMZZMvlX3nhDDO4AJXWq0GCtEciZX5IPhuG5Nk%3D"

    def get_mouser_cookies(self) -> Dict[str, str]:
        """Get Mouser-specific cookies with fallback."""
        fallback_cookies = {
            # Core Mouser cookies
            "preferences": "pl=en-GB&pc_au=AUD&pc_www=USDu",
            "ASP.NET_SessionId": "vpdrbymoksobh3fkxkxmzxqd",
            "CARTCOOKIEUUID": "b6325627-66f5-43e1-b728-b6d98599a50e",
            "__RequestVerificationToken": "li_FRTfMsLN8rv6xqUQGK8NkParHaNBc9XI5kPJYsCuMkyzkyDbSSMAV1_nVYFHtQ9XddJgpTnjy6P6f6dP8CTkOGdw1",
            # Bot detection / security cookies (CRITICAL)
            "datadome": "zbrQA3K7wQwcoYxOaihpS6aD82indE3gJffIw5YZlyLsp6rzLDa3lQlyx38FtI8cvNLD4Rljt0rfDHFHnNJFspxVJC~~xo8hKjEIE4P1qnN8Yalhndyv6XFNMF1cz_tK",
            "akacd_Default_PR": "3930561630~rv=46~id=97ea4d7ebb206f790d525ae0a1764aa8",
            "_abck": "EBEFD423EA257F8875C9324F7899376D~-1~YAAQpm44F0/fVBaYAQAA1r6hLw7bWr6VqeqQyw2DzV/mi8rWw+ELkWcyogh6CQ2ac3DMYAEtFm3Tu3/lR/3pHo41XBTk6p7qx3j7wUGcE4M5X9FJ1FWOTREBBxP8qhl8OYcxIkLmmoJT/uSW1PVWbS6sMzSC/IQ46nlT53J4KZIjXhSrlIKAHaIbTN8kDljhsbYt7vNt2Ox0W3CfAOXr0QX47vq8zKScKjwhBxSMGQerw0qvTLy5sE9GoJMfIod9pfHF/hZ2uVqLrtCuSkOjX9wzoGOPaiwm9FVaL0tvUmFKCtvw18f+PP9BurSIdC47Op9oUcp59WKawVFrFdUGCqjWE7r2uTZnxeSitecJG0aH/J5crhd6FgNjojzOaMvyddbaHu9msC05P9Iwb2ZC/Dzlw9SoKXmVKf0riRFp5MOAAKH+dOvfv9ni22D1RKT//wG9QFreYC8D+/A9Rej60CmTZALHOlJbtBkhxxI2NdHjCOiT4FJ/FnM0NfASaLB1eV51d8Ieqx6Tw6PwtiO/xHGCcQYOsbgxjaUE3As6WYLNjmnZpR75Ne1Sho0LBvktEmFuDAso/rOY6hsCZehSb7BnuAmbo2+u21+aPDJ6lT5K9GgukW8+7uuz1xDD+KY75VZFgZqIvsSy40U0nY75lm0twcwTli9r8gnCB7ziSS95iYWZ2Sq6jykEAujZkYh/SGIfmQb5WISkmbLOKYHJagLnOh4QddPjHWy6mbcuzfjRNcfYh/bYk06xn+tZfCUXw6uMng==~-1~-1~-1",
            "bm_s": "YAAQpm44FxbfVBaYAQAAV7yhLwOEa7AEZ/cQr6za0Kyj3862wfRb+DhU6/KxCgnCwyaw9Z4WFXE4FzE7urse4bgRsBmHk1Si+olT3+mHgNPDxHBlmS6o4QjMsLvrx2re01MDrwmhUvhmp+XMNcW5S9dmBVwI+MWFwynMv3YVV5KnLLU5FgRQPOR5/MqX/HcZBAEGowFJJ+mCYCq59LkviZVwUlRRYlBn7hXuZPp8+/kdjoir31a+re3z31MmN0dmC3jTo7oQ1OL3Ld3Yb7j2tt7YLKb2mMjDiscm7M76zwowY3yp3xjmwY5BlXpmRMSi93jr87iT19tLuncJNyCNNQLOFmfp/e5SdLVxuPNYxOYXDX9/x4aQ0Vri43PGYH/CPK5PGYWSnyaRcxLb23iriMNY8FAoYt5RKVw5lohbvJxru7fcutS0kbOSW8Z5GH9ARdxjyRsh3Xi/cCsHLWnIHECtOpX1OY2WxPxZ9hsjshKELV/cLdSAGtHaBUxF293/Ni/r9U/n30ndBI3KN6ovVmsAN2K9WXDm4TKm/i/V1M3sRwpG/zmTBdOSVADJG3UE9nRgUMUycFRL85o/92pK",
            "bm_so": "3DCEB8E55019E09B3654632D67A74A45726B8C7C48FB36C50280785F5AF0A3BC~YAAQpm44F6veVBaYAQAAkrmhLwSNhJ0j+ys9NSrgLUk0MQTIvTcIOfEVgOM6/EI4ie0tUjZZ9QgLnZXWdqmpMVdKXSWWqUH5vxOns+BpanDmh3AESzKsBcP7jHzSiSWmp2hsaQB6l3OqlKXBaswn1QMxIxjBfJOMKqZPUo4BaaMm6p/2X4NDTOQ7OWZwlNiaQrbcrtku7EcETSe8JGPtGqBOrhp4Uj23+dkLOiCBzlRQmj81lPf6fYyGizQQSEy/osfk3lZ44zRvaaFf5xwE0a+SjYRnU9kmku6T4TGjTOKJu3KM6gygrWU+48TEJy5asJIqq/av0eWwIO7aNBZHHS23khBBOfhqTzzNoH2GpJISwwndBZgki/q9qp2POmrroIOMB0bx4ZA3yRdVJVO8S+k7K1kQv8d+Y5+aAYaTBdwtHFQXDcZERTk6tYHlcPGjDSz9f0NzSEg5/wgAdXuH",
            "bm_lso": "3DCEB8E55019E09B3654632D67A74A45726B8C7C48FB36C50280785F5AF0A3BC~YAAQpm44F6veVBaYAQAAkrmhLwSNhJ0j+ys9NSrgLUk0MQTIvTcIOfEVgOM6/EI4ie0tUjZZ9QgLnZXWdqmpMVdKXSWWqUH5vxOns+BpanDmh3AESzKsBcP7jHzSiSWmp2hsaQB6l3OqlKXBaswn1QMxIxjBfJOMKqZPUo4BaaMm6p/2X4NDTOQ7OWZwlNiaQrbcrtku7EcETSe8JGPtGqBOrhp4Uj23+dkLOiCBzlRQmj81lPf6fYyGizQQSEy/osfk3lZ44zRvaaFf5xwE0a+SjYRnU9kmku6T4TGjTOKJu3KM6gygrWU+48TEJy5asJIqq/av0eWwIO7aNBZHHS23khBBOfhqTzzNoH2GpJISwwndBZgki/q9qp2POmrroIOMB0bx4ZA3yRdVJVO8S+k7K1kQv8d+Y5+aAYaTBdwtHFQXDcZERTk6tYHlcPGjDSz9f0NzSEg5/wgAdXuH^1753145785443",
            "bm_sz": "26DE1D9666B1E30AB122583F0EAD0DFF~YAAQpm44F6zeVBaYAQAAkrmhLxy/u0YSi9F3LQmGOFc4Q2JLp+Tsae3ehBPJB2hc6TAFJqYgMj2UDOkBcvO/u4UKkoqL2T3M4yW6lYDzaLkJfz+1pxIyXttffPCI6B9GRCNFlHHD6vMzkoFoI3vTC5dXsRljzu8092MH4BwiiSFBQNHMLLb5oSUyZo9psikRNGNE2iIU+DQQy8GY0Hp8G+XkW2v5DTuKSjXqYooOTZ+EyvWo9EJVRhtxlthEiC5CW8tTvTOM85l0RSuYqRU2dUXhI2ySnt4OSVRYVHVTB8Hkf1e1T5L1Wy6PdeFgLuJ6yXexk3YWbCiCAnErQ3TUOMdXKjBGOgmbpvWdAmrQKKlCdIVoSiryyC9GLrbFP0h3itj3p3to9533OBl3sjiiX2CKZx5mM5WvNAcwqaFu+Vdwmme8Zda4+5C0tulaVxLxlglcDc4HLCCDHHWq3y6RDUK1YtxOguixeCfE~3158067~3686966",
            "ak_bmsc": "9B7B4C3AAF98A94A92521D47042CFFAB~000000000000000000000000000000~YAAQpm44FwC9TxaYAQAAY3lxLxzxoDTBalF72uLFhdrSwk1yBA//KkwSqVc94nQfyeVMN2TVy7HICTlBG090qI8lDzc4OzgK/5WgSX0IhTlxPbb7EvdrCnBE10/XdieYC+m9Mr6jLXhrLFcU4HeP8wjzWY6HiEFBSGWaw7xdhBvSqeyC+0UZa8PbG3FiGY2bX9DPCZL+COKlfUWwJksi3LKsCec3SWg3xmsnHl9y8jtp1Lq8Kqvd2Qehwcn3E3+dcjbjlwS/puqbNXBo/CrocFbwNay614wP3KNfQ4S0ZCwWienZLqk+J3XFkOYCCL2FaaFGO9A8Vwc62hNwOCGbVjp9MULvfWZ9OPFjZ83Mo3WK2+kvKjS892Nhd0oS3157DWJpbb5BgllpMhQEamyG+JiSyeEHiS6PpD9u3k+9JpJhkfglaqPU1El3U/bCzfRfzFtjeNpTi68zn6Rkdw==",
            "AKA_A2": "A",
            "bm_ss": "ab8e18ef4e",
            # Analytics and tracking cookies
            "_gcl_au": "1.1.1269973529.1753108853",
            "_ga": "GA1.2.2049715743.1753108854",
            "_gid": "GA1.2.1371314716.1753108855",
            "_fbp": "fb.1.1753108855525.228745913527996129",
            "VisitorID": "da1ae1e4-714d-4dc1-9d16-68805be3d3f2",
            "_rdt_uuid": "1753108854754.a9739ab8-da05-4859-948d-2ee63bc69f09",
            # Consent and session cookies
            "OptanonConsent": "isGpcEnabled=0&datestamp=Tue+Jul+22+2025+10%3A56%3A25+GMT%2B1000+(Australian+Eastern+Standard+Time)&version=202501.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=dceb302e-e50a-44c0-9887-dd94039b2b70&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0004%3A1%2CC0002%3A1%2CC0001%3A1&AwaitingReconsent=false&geolocation=AU%3BQLD",
            "OptanonAlertBoxClosed": "2025-07-22T00:56:25.148Z",
            "__neoui": "30e86740-eef8-40c5-9e96-7a3aa50330e0",
            "PIM-SESSION-ID": "DnkxoBRaMxxKWPwa",
            "RT": "z=1&dm=mouser.com&si=0c3599ea-1f79-480e-9878-1a96c4fa3e1d&ss=mddruniq&sl=6&tt=af5&bcn=%2F%2F684d0d45.akstat.io%2F&obo=2&hd=1vtd0",
            "_ga_15W4STQT4T": "GS2.1.s1753142621$o2$g1$t1753145786$j2$l0$h0",
            "_ga_P029W6H4P4": "GS2.1.s1753145728$o1$g0$t1753145728$j60$l0$h0",
            "fs_uid": "#Z1BBJ#b91d1ad4-8f36-4489-a413-1e2c051a3677:23bdc3aa-5589-4c93-9fbe-bdb6cb987c50:1753141437993::9#/1784644875",
            "LPVID": "E4M2VlZGUzM2QyNDlmNGEw",
            "LPSID-12757882": "Nl_O4WN1QJqxi1nbyq-W-g",
            "QSI_HistorySession": "https%3A%2F%2Fau.mouser.com%2FProductDetail%2FAmphenol-RF%2F242125-10%3Fqs%3DsGAEpiMZZMvlX3nhDDO4AJXWq0GCtEciZX5IPhuG5Nk%253D~1753108859043%7Chttps%3A%2F%2Fau.mouser.com%2Fservicesandtools%2F~1753142625791%7Chttps%3A%2F%2Fau.mouser.com%2FMyAccount%2FMouserLogin%3Fqs%3D0gZ0gv0KDwtfpH7TYoEeG1RQJL7wb2DL~1753142629484%7Chttps%3A%2F%2Fau.mouser.com%2Fapi-hub%2F~1753142631554%7Chttps%3A%2F%2Fau.mouser.com%2Fapi-search%2F~1753142648541%7Chttps%3A%2F%2Fau.mouser.com%2FProductDetail%2FAmphenol-RF%2F242125-10%3Fqs%3DsGAEpiMZZMvlX3nhDDO4AJXWq0GCtEciZX5IPhuG5Nk%253D~1753143056537%7Chttps%3A%2F%2Fau.mouser.com%2FProductDetail%2FAmphenol-RF%2F242125-10~1753145786373",
            "fs_lua": "1.1753145729306",
            "_fs_dwell_passed": "23bdc3aa-5589-4c93-9fbe-bdb6cb987c50",
        }

        return self.get_valid_cookies(fallback_cookies)


# Factory function for easy usage
def create_cookie_manager(vendor: str, **kwargs) -> CookieManager:
    """
    Create a cookie manager for a specific vendor.

    Args:
        vendor: Vendor name ("mouser", "digikey", etc.)
        **kwargs: Additional arguments for the cookie manager

    Returns:
        Appropriate cookie manager instance
    """
    vendor_lower = vendor.lower()

    if vendor_lower == "mouser":
        return MouserCookieManager(**kwargs)
    else:
        # Generic cookie manager for other vendors
        return CookieManager(vendor_name=vendor, **kwargs)
