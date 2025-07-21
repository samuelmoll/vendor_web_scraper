"""
BOM to InvenTree mapping utilities.

This module provides mapping functions for converting BOM data
to InvenTree-compatible format based on scraped product information.
"""

import json
from typing import Dict, Any, Optional, Callable


def create_bom_mapping_dict() -> Dict[str, Callable]:
    """
    Create a dictionary with BOM headers as keys and BOM header functions as values.

    The functions take a ProductInfo object and return the appropriate value
    for the corresponding InvenTree field.

    Returns:
        Dictionary mapping BOM field names to extraction functions
    """


"""
BOM to InvenTree mapping utilities.

This module provides mapping functions for converting BOM data
to InvenTree-compatible format based on scraped product information.
"""

import json
from typing import Dict, Any, Optional, Callable


def create_bom_mapping_dict() -> Dict[str, Callable]:
    """
    Create a dictionary with BOM headers as keys and BOM header functions as values.

    The functions take a ProductInfo object and return the appropriate value
    for the corresponding InvenTree field.

    Returns:
        Dictionary mapping BOM field names to extraction functions
    """

    def extract_name(product: Any) -> str:
        """
        Extract product name (usually shorter than description).

        Uses the first few words of the title/description or manufacturer part number.
        """
        if not product or not hasattr(product, "specifications"):
            return "Unknown Product"

        # Try manufacturer part number first (often shorter)
        if (
            hasattr(product.specifications, "manufacturer_part_number")
            and product.specifications.manufacturer_part_number
        ):
            return product.specifications.manufacturer_part_number

        # Use first few words of title/description
        title = getattr(product, "title", "") or ""
        words = title.split()
        if len(words) > 4:
            return " ".join(words[:4])
        return title or "Unknown Product"

    def extract_description(product: Any) -> str:
        """Extract full product description."""
        if not product:
            return ""

        # Use specifications description first, fallback to title
        if hasattr(product, "specifications") and product.specifications:
            if hasattr(product.specifications, "description") and product.specifications.description:
                return product.specifications.description
        return getattr(product, "title", "") or ""

    def extract_brand(product: Any) -> str:
        """Extract manufacturer/brand name."""
        if not product or not hasattr(product, "specifications"):
            return ""
        return getattr(product.specifications, "manufacturer", "") or ""

    def extract_remote_image(product: Any) -> str:
        """Extract product image URL."""
        if not product or not hasattr(product, "media"):
            return ""
        return getattr(product.media, "primary_image_url", "") or ""

    def extract_keywords(product: Any) -> str:
        """Extract keywords (categories) as comma-separated string."""
        if not product or not hasattr(product, "specifications"):
            return ""

        keywords = []

        # Add category if available
        if hasattr(product.specifications, "category") and product.specifications.category:
            keywords.append(product.specifications.category)

        # Add manufacturer if available
        if hasattr(product.specifications, "manufacturer") and product.specifications.manufacturer:
            keywords.append(product.specifications.manufacturer)

        # Add key technical specs as keywords
        if hasattr(product.specifications, "technical_specs") and product.specifications.technical_specs:
            for key, value in product.specifications.technical_specs.items():
                if key.lower() in ["type", "series", "material", "colour", "color"]:
                    keywords.append(f"{key}: {value}")

        return ", ".join(keywords)

    def extract_link(product: Any) -> str:
        """Extract product URL."""
        if not product:
            return ""
        return getattr(product, "product_url", "") or ""

    def extract_units(product: Any) -> int:
        """
        Extract number of items per item (usually 1 for individual components).

        This looks for pack quantities or minimum order quantities.
        """
        if not product or not hasattr(product, "pricing"):
            return 1

        # Check for minimum order quantity
        if hasattr(product.pricing, "minimum_order_quantity") and product.pricing.minimum_order_quantity:
            return product.pricing.minimum_order_quantity

        # Default to 1 for individual components
        return 1

    def extract_pricing_updated(product: Any) -> str:
        """Extract current price with currency."""
        if not product or not hasattr(product, "pricing"):
            return ""

        if hasattr(product.pricing, "unit_price") and product.pricing.unit_price:
            currency = getattr(product.pricing, "currency", "USD") or "USD"
            return f"{currency} {product.pricing.unit_price}"

        return ""

    def extract_in_stock(product: Any) -> bool:
        """Extract stock availability status."""
        if not product or not hasattr(product, "availability"):
            return False
        return getattr(product.availability, "in_stock", False) or False

    def extract_lead_time(product: Any) -> Optional[str]:
        """Extract lead time information."""
        if not product or not hasattr(product, "availability"):
            return None

        if hasattr(product.availability, "lead_time_description") and product.availability.lead_time_description:
            return product.availability.lead_time_description
        elif hasattr(product.availability, "lead_time_days") and product.availability.lead_time_days:
            return f"{product.availability.lead_time_days} days"

        return None

    def extract_external_stock(product: Any) -> Optional[int]:
        """Extract available stock quantity."""
        if not product or not hasattr(product, "availability"):
            return None
        return getattr(product.availability, "stock_quantity", None)

    def extract_parameters(product: Any) -> str:
        """
        Extract technical parameters as JSON string.

        This includes all technical specifications in a structured format.
        """
        if not product or not hasattr(product, "specifications"):
            return "{}"

        parameters = {}

        # Add basic product info
        if hasattr(product.specifications, "manufacturer") and product.specifications.manufacturer:
            parameters["Brand"] = product.specifications.manufacturer

        if (
            hasattr(product.specifications, "manufacturer_part_number")
            and product.specifications.manufacturer_part_number
        ):
            parameters["Manufacturer Part Number"] = product.specifications.manufacturer_part_number

        if hasattr(product.specifications, "category") and product.specifications.category:
            parameters["Category"] = product.specifications.category

        # Add technical specifications
        if hasattr(product.specifications, "technical_specs") and product.specifications.technical_specs:
            parameters.update(product.specifications.technical_specs)

        # Add pricing info if available
        if hasattr(product, "pricing") and product.pricing:
            if hasattr(product.pricing, "unit_price") and product.pricing.unit_price:
                currency = getattr(product.pricing, "currency", "USD") or "USD"
                parameters["Unit Price"] = f"{currency} {product.pricing.unit_price}"

            if hasattr(product.pricing, "minimum_order_quantity") and product.pricing.minimum_order_quantity:
                parameters["Minimum Order Quantity"] = product.pricing.minimum_order_quantity

        # Add availability info
        if hasattr(product, "availability") and product.availability:
            if hasattr(product.availability, "stock_quantity") and product.availability.stock_quantity:
                parameters["Stock Quantity"] = product.availability.stock_quantity

            if hasattr(product.availability, "lead_time_description") and product.availability.lead_time_description:
                parameters["Lead Time"] = product.availability.lead_time_description

        return json.dumps(parameters, indent=2)

    # Return the mapping dictionary
    return {
        "name": extract_name,
        "description": extract_description,
        "brand": extract_brand,
        "remote_image": extract_remote_image,
        "keywords": extract_keywords,
        "link": extract_link,
        "units": extract_units,
        "pricing_updated": extract_pricing_updated,
        "in_stock": extract_in_stock,
        "lead_time": extract_lead_time,
        "external_stock": extract_external_stock,
        "parameters": extract_parameters,
    }


def convert_product_to_bom_row(product: Any) -> Dict[str, Any]:
    """
    Convert a ProductInfo object to a BOM row dictionary.

    Args:
        product: ProductInfo object from scraping

    Returns:
        Dictionary with BOM field names as keys and extracted values
    """
    mapping = create_bom_mapping_dict()
    result = {}

    for field_name, extract_func in mapping.items():
        try:
            result[field_name] = extract_func(product)
        except Exception as e:
            print(f"Warning: Failed to extract {field_name}: {e}")
            result[field_name] = None

    return result


def create_inventree_excel_row(product: Any) -> Dict[str, Any]:
    """
    Create an InvenTree-compatible Excel row from ProductInfo.

    This maps the scraped data to the expected InvenTree import format.

    Args:
        product: ProductInfo object from scraping

    Returns:
        Dictionary ready for Excel export to InvenTree
    """
    bom_data = convert_product_to_bom_row(product)

    # Map to InvenTree expected field names
    inventree_row = {
        "IPN": bom_data.get("name", ""),
        "Name": bom_data.get("description", ""),
        "Description": bom_data.get("description", ""),
        "Category": bom_data.get("keywords", "").split(",")[0] if bom_data.get("keywords") else "",
        "Supplier Name": getattr(product, "vendor_name", "") if product else "",
        "SKU": getattr(product, "vendor_part_number", "") if product else "",
        "MPN": bom_data.get("name", ""),
        "Manufacturer": bom_data.get("brand", ""),
        "Link": bom_data.get("link", ""),
        "Note": bom_data.get("parameters", ""),
        "Image": bom_data.get("remote_image", ""),
        "Units": bom_data.get("units", 1),
        "Price": bom_data.get("pricing_updated", ""),
        "In Stock": bom_data.get("in_stock", False),
        "Lead Time": bom_data.get("lead_time", ""),
        "Stock Quantity": bom_data.get("external_stock", ""),
    }

    return inventree_row
