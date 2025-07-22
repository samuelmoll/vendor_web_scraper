"""
Product information data model using Pydantic for validation and serialization.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from pydantic import field_validator, ConfigDict, BaseModel, Field, HttpUrl, model_validator


class ProductPricing(BaseModel):
    """Product pricing information"""

    currency: str = Field(..., description="Currency code (e.g., 'USD', 'EUR')")

    # Package-level pricing (what you actually buy)
    package_price: Optional[Decimal] = Field(
        None, description="Price per package/sellable unit (e.g., price for 1 bag of 100 screws)"
    )
    package_price_inc_tax: Optional[Decimal] = Field(None, description="Package price including tax")
    package_quantity: Optional[int] = Field(
        1, description="Number of individual items in one package (e.g., 100 screws per bag)"
    )
    package_unit: Optional[str] = Field(
        None, description="What constitutes one package (e.g., 'bag', 'reel', 'box', 'each')"
    )

    # Unit-level pricing (cost per individual item)
    unit_price: Optional[Decimal] = Field(
        None, description="Price per individual item (calculated: package_price / package_quantity)"
    )
    unit_price_inc_tax: Optional[Decimal] = Field(None, description="Unit price including tax")

    # Ordering constraints
    minimum_order_quantity: Optional[int] = Field(None, description="Minimum number of packages to order")
    order_multiple: Optional[int] = Field(None, description="Must order in multiples of this many packages")

    # Volume pricing
    quantity_breaks: Dict[int, Decimal] = Field(
        default_factory=dict, description="Package quantity-based pricing tiers"
    )

    @model_validator(mode="before")
    @classmethod
    def calculate_derived_fields(cls, values):
        """Calculate derived pricing fields before validation"""
        if isinstance(values, dict):
            # Auto-calculate unit_price if not provided
            if values.get("unit_price") is None:
                package_price = values.get("package_price")
                package_quantity = values.get("package_quantity", 1)

                if package_price is not None and package_quantity and package_quantity > 0:
                    try:
                        unit_price = Decimal(str(package_price)) / Decimal(str(package_quantity))
                        values["unit_price"] = unit_price.quantize(Decimal("0.0001"))
                    except (ValueError, TypeError, InvalidOperation):
                        pass  # Let field validator handle the error

            # Auto-calculate unit_price_inc_tax if not provided
            if values.get("unit_price_inc_tax") is None and values.get("unit_price") is not None:
                try:
                    unit_price = Decimal(str(values["unit_price"]))
                    # Assume 10% GST
                    values["unit_price_inc_tax"] = (unit_price * Decimal("1.1")).quantize(Decimal("0.01"))
                except (ValueError, TypeError, InvalidOperation):
                    pass

        return values

    @field_validator("unit_price", "package_price", "unit_price_inc_tax", "package_price_inc_tax", mode="before")
    @classmethod
    def validate_decimal_fields(cls, v):
        """Ensure pricing values are valid decimals"""
        if v is None:
            return None
        try:
            return Decimal(str(v))
        except (ValueError, TypeError, InvalidOperation):
            raise ValueError(f"Invalid decimal value: {v}")

    @field_validator("quantity_breaks", mode="before")
    @classmethod
    def validate_quantity_breaks(cls, v):
        """Ensure quantity breaks are valid"""
        if not isinstance(v, dict):
            return {}

        validated_breaks = {}
        for k, val in v.items():
            try:
                quantity = int(k) if not isinstance(k, int) else k
                price = Decimal(str(val)) if val is not None else None
                if quantity > 0 and price is not None:
                    validated_breaks[quantity] = price
            except (ValueError, TypeError, InvalidOperation):
                continue  # Skip invalid entries

        return validated_breaks


class ProductSpecifications(BaseModel):
    """Technical specifications and parameters"""

    manufacturer: Optional[str] = None
    manufacturer_part_number: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    detailed_description: Optional[str] = None
    technical_specs: Dict[str, Any] = Field(default_factory=dict)
    datasheet_url: Optional[HttpUrl] = None
    compliance_certifications: List[str] = Field(default_factory=list)
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ProductAvailability(BaseModel):
    """Stock and availability information"""

    in_stock: Optional[bool] = None
    stock_quantity: Optional[int] = None
    lead_time_days: Optional[int] = None
    lead_time_description: Optional[str] = None
    discontinued: bool = False
    lifecycle_status: Optional[str] = None  # e.g., "Active", "NRND", "Obsolete"


class ProductMedia(BaseModel):
    """Product images and media"""

    primary_image_url: Optional[HttpUrl] = None
    additional_images: List[HttpUrl] = Field(default_factory=list)
    video_urls: List[HttpUrl] = Field(default_factory=list)


class ProductInfo(BaseModel):
    """
    Comprehensive product information model for vendor scraping.

    This model serves as the standard format for all scraped product data,
    ensuring consistency across different vendor scrapers.
    """

    # Basic identification
    vendor_name: str = Field(..., description="Name of the vendor (e.g., 'RS Components')")
    vendor_part_number: str = Field(..., description="Vendor's part number/SKU")
    product_url: HttpUrl = Field(..., description="URL of the product page")

    # Product details
    title: str = Field(..., description="Product title/name")
    specifications: ProductSpecifications = Field(default_factory=ProductSpecifications)
    pricing: ProductPricing = Field(..., description="Pricing information")
    availability: ProductAvailability = Field(default_factory=ProductAvailability)
    media: ProductMedia = Field(default_factory=ProductMedia)

    # Additional data
    vendor_specific_data: Dict[str, Any] = Field(
        default_factory=dict, description="Vendor-specific fields that don't fit standard model"
    )

    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.now)
    scraper_version: Optional[str] = None
    # TODO[pydantic]: The following keys were removed: `json_encoders`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(
        extra="allow",
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v) if v is not None else None,
            HttpUrl: lambda v: str(v) if v is not None else None,
        },
    )

    def to_inventree_format(self) -> Dict[str, Any]:
        """
        Convert product info to InvenTree-compatible format.

        Returns:
            Dictionary with InvenTree field mappings
        """
        return {
            "name": self.title,
            "description": self.specifications.description or self.title,
            "IPN": self.specifications.manufacturer_part_number or self.vendor_part_number,
            "category_name": self.specifications.category,
            "link": str(self.product_url),
            "remote_image": str(self.media.primary_image_url) if self.media.primary_image_url else None,
            "notes": str(
                self.specifications.detailed_description
                + f"\n\nScraped from {self.vendor_name} on {self.scraped_at.isoformat()}"
                if self.specifications.detailed_description
                else f"Scraped from {self.vendor_name} on {self.scraped_at.isoformat()}"
            ),
            "default_supplier": self.vendor_name,
            "base_cost": float(self.pricing.unit_price) if self.pricing.unit_price else None,
            "units": self.pricing.packaging or None,
            "in_stock": self.availability.in_stock,
            "minimum_stock": self.pricing.minimum_order_quantity or 1,  # TODO: Check if this is correct
            "stock": self.availability.stock_quantity or 0,
            "purchaseable": True,
            "active": not self.availability.discontinued,
            "component": True,
            "trackable": False,
            "keywords": f"{self.vendor_name},{self.specifications.manufacturer or ''}",
            "creation_date": self.scraped_at.isoformat(),
        }

    def to_excel_row(self) -> Dict[str, Any]:
        """
        Convert product info to Excel-friendly row format.

        Returns:
            Dictionary suitable for pandas DataFrame
        """
        return {
            "Vendor": self.vendor_name,
            "Vendor Part Number": self.vendor_part_number,
            "Product Title": self.title,
            "Manufacturer": self.specifications.manufacturer,
            "Manufacturer Part Number": self.specifications.manufacturer_part_number,
            "Category": self.specifications.category,
            "Description": self.specifications.description,
            "Unit Price": float(self.pricing.unit_price) if self.pricing.unit_price else None,
            "Currency": self.pricing.currency,
            "MOQ": self.pricing.minimum_order_quantity,
            "In Stock": self.availability.in_stock,
            "Stock Quantity": self.availability.stock_quantity,
            "Lead Time (Days)": self.availability.lead_time_days,
            "Product URL": str(self.product_url),
            "Image URL": str(self.media.primary_image_url) if self.media.primary_image_url else None,
            "Scraped At": self.scraped_at.isoformat(),
        }
