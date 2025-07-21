"""
Excel exporter for product data using pandas and openpyxl.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd

from .base_exporter import BaseExporter
from ..core.product_model import ProductInfo


class ExcelExporter(BaseExporter):
    """
    Exporter that creates Excel files from scraped product data.

    Uses pandas and openpyxl to create formatted Excel files with
    multiple sheets for different data aspects.
    """

    def __init__(self, output_path: Optional[Path] = None):
        """
        Initialize Excel exporter.

        Args:
            output_path: Directory where Excel files should be saved
        """
        super().__init__(output_path)
        self.sheet_configs = {
            "Products": {
                "columns": [
                    "Vendor",
                    "Vendor Part Number",
                    "Product Title",
                    "Manufacturer",
                    "Manufacturer Part Number",
                    "Category",
                    "Description",
                    "Unit Price",
                    "Currency",
                    "MOQ",
                    "In Stock",
                    "Stock Quantity",
                    "Lead Time (Days)",
                    "Product URL",
                    "Image URL",
                    "Scraped At",
                ]
            }
        }

    def export_single(self, product_info: ProductInfo) -> Dict[str, Any]:
        """
        Convert single product to Excel row format.

        Args:
            product_info: Product information to export

        Returns:
            Dictionary representing an Excel row
        """
        return product_info.to_excel_row()

    def export_multiple(self, products: List[ProductInfo]) -> pd.DataFrame:
        """
        Convert multiple products to pandas DataFrame.

        Args:
            products: List of product information to export

        Returns:
            pandas DataFrame ready for Excel export
        """
        if not products:
            return pd.DataFrame()

        rows = [self.export_single(product) for product in products]
        df = pd.DataFrame(rows)

        # Reorder columns according to configuration
        available_columns = [col for col in self.sheet_configs["Products"]["columns"] if col in df.columns]

        # Add any additional columns not in the standard config
        extra_columns = [col for col in df.columns if col not in available_columns]
        all_columns = available_columns + extra_columns

        return df[all_columns]

    def save_to_file(self, data: Any, filename: Optional[str] = None) -> Path:
        """
        Save DataFrame to Excel file.

        Args:
            data: pandas DataFrame to save
            filename: Optional filename

        Returns:
            Path to saved file
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Excel exporter requires pandas DataFrame")

        if filename is None:
            filename = self.get_default_filename("xlsx")

        if self.output_path:
            file_path = self.output_path / filename
        else:
            file_path = Path(filename)

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create Excel writer with formatting
        with pd.ExcelWriter(file_path, engine="openpyxl", options={"remove_timezone": True}) as writer:
            # Write main products sheet
            data.to_excel(writer, sheet_name="Products", index=False, freeze_panes=(1, 0))  # Freeze header row

            # Format the worksheet
            workbook = writer.book
            worksheet = writer.sheets["Products"]

            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter

                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass

                # Set column width with reasonable limits
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

            # Add summary sheet if multiple products
            if len(data) > 1:
                self._add_summary_sheet(writer, data)

        return file_path

    def _add_summary_sheet(self, writer, df: pd.DataFrame) -> None:
        """
        Add a summary sheet with statistics.

        Args:
            writer: Excel writer object
            df: DataFrame with product data
        """
        summary_data = {
            "Metric": [
                "Total Products",
                "Unique Vendors",
                "Unique Manufacturers",
                "Products with Pricing",
                "Products In Stock",
                "Average Price",
                "Price Range (Min)",
                "Price Range (Max)",
            ],
            "Value": [
                len(df),
                df["Vendor"].nunique() if "Vendor" in df.columns else 0,
                df["Manufacturer"].nunique() if "Manufacturer" in df.columns else 0,
                df["Unit Price"].notna().sum() if "Unit Price" in df.columns else 0,
                df["In Stock"].sum() if "In Stock" in df.columns else 0,
                df["Unit Price"].mean() if "Unit Price" in df.columns else 0,
                df["Unit Price"].min() if "Unit Price" in df.columns else 0,
                df["Unit Price"].max() if "Unit Price" in df.columns else 0,
            ],
        }

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

    def export_to_inventree_format(self, products: List[ProductInfo]) -> pd.DataFrame:
        """
        Export products in InvenTree-compatible format.

        Args:
            products: List of products to export

        Returns:
            DataFrame formatted for InvenTree import
        """
        if not products:
            return pd.DataFrame()

        inventree_rows = [product.to_inventree_format() for product in products]
        return pd.DataFrame(inventree_rows)
