"""
Base exporter for converting scraped product data to various formats.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..core.product_model import ProductInfo


class BaseExporter(ABC):
    """
    Abstract base class for exporting product data to different formats.
    
    Exporters convert ProductInfo objects to various output formats like
    Excel, CSV, JSON, or direct API integration with systems like InvenTree.
    """
    
    def __init__(self, output_path: Optional[Path] = None):
        """
        Initialize the exporter.
        
        Args:
            output_path: Path where exported data should be saved
        """
        self.output_path = output_path
    
    @abstractmethod
    def export_single(self, product_info: ProductInfo) -> Dict[str, Any]:
        """
        Export a single product to the target format.
        
        Args:
            product_info: Product information to export
            
        Returns:
            Dictionary containing the exported data
        """
        pass
    
    @abstractmethod
    def export_multiple(self, products: List[ProductInfo]) -> Any:
        """
        Export multiple products to the target format.
        
        Args:
            products: List of product information to export
            
        Returns:
            Exported data in the appropriate format
        """
        pass
    
    @abstractmethod
    def save_to_file(self, data: Any, filename: Optional[str] = None) -> Path:
        """
        Save exported data to file.
        
        Args:
            data: Data to save
            filename: Optional filename, will generate if not provided
            
        Returns:
            Path to the saved file
        """
        pass
    
    def get_default_filename(self, extension: str) -> str:
        """
        Generate a default filename with timestamp.
        
        Args:
            extension: File extension (without dot)
            
        Returns:
            Default filename
        """
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"scraped_products_{timestamp}.{extension}"
