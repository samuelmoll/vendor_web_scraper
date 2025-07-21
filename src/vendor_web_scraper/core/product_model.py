"""
Product information data model using Pydantic for validation and serialization.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from pydantic import field_validator, ConfigDict, BaseModel, Field, HttpUrl


class ProductPricing(BaseModel):
    """Product pricing information"""

    currency: str = Field(..., description="Currency code (e.g., 'USD', 'EUR')")
    unit_price: Optional[Decimal] = Field(None, description="Price per unit (No GST)")
    unit_price_inc_tax: Optional[Decimal] = Field(None, description="Price per unit (GST)")
    quantity_breaks: Dict[int, Decimal] = Field(default_factory=dict, description="Quantity-based pricing tiers")
    minimum_order_quantity: Optional[int] = Field(None, description="Minimum order quantity")
    price_per_unit: Optional[str] = Field(None, description="Unit of pricing (e.g., 'each', 'meter')")

    @field_validator("unit_price", "quantity_breaks", mode="before")
    @classmethod
    def validate_pricing(cls, v):
        """Ensure pricing values are valid decimals"""
        if isinstance(v, dict):
            return {k: Decimal(str(val)) if val is not None else None for k, val in v.items()}
        return Decimal(str(v)) if v is not None else None


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
            "units": self.pricing.price_per_unit or "each",
            "in_stock": self.availability.in_stock,
            "minimum_stock": self.pricing.minimum_order_quantity or 1,
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
