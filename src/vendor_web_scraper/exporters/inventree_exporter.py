"""
InvenTree API exporter for direct integration with InvenTree instances.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from .base_exporter import BaseExporter
from ..core.product_model import ProductInfo


class InvenTreeExporter(BaseExporter):
    """
    Exporter that directly integrates with InvenTree via API.
    
    Can create parts, suppliers, and manufacturer parts directly
    in an InvenTree instance, or export to InvenTree-compatible formats.
    """
    
    def __init__(
        self, 
        output_path: Optional[Path] = None,
        api_url: Optional[str] = None,
        api_token: Optional[str] = None,
        create_missing_categories: bool = True,
        create_missing_suppliers: bool = True
    ):
        """
        Initialize InvenTree exporter.
        
        Args:
            output_path: Path for file exports
            api_url: InvenTree API URL
            api_token: InvenTree API token
            create_missing_categories: Create categories if they don't exist
            create_missing_suppliers: Create suppliers if they don't exist
        """
        super().__init__(output_path)
        self.api_url = api_url
        self.api_token = api_token
        self.create_missing_categories = create_missing_categories
        self.create_missing_suppliers = create_missing_suppliers
        self.logger = logging.getLogger(__name__)
        
        # Try to initialize InvenTree API if credentials provided
        self.api = None
        if api_url and api_token:
            self._initialize_api()
    
    def _initialize_api(self):
        """Initialize InvenTree API connection."""
        try:
            # Import here to make it optional
            from inventree.api import InvenTreeAPI
            
            self.api = InvenTreeAPI(
                host=self.api_url,
                token=self.api_token
            )
            assert self.api is not None, "Failed to initialize InvenTree API"
            
            # Test connection
            self.api.checkConnection()
            self.logger.info("Successfully connected to InvenTree API")
            
        except ImportError:
            self.logger.warning(
                "InvenTree library not installed. File export only."
            )
        except Exception as e:
            self.logger.error(f"Failed to connect to InvenTree API: {e}")
            self.api = None
    
    def export_single(self, product_info: ProductInfo) -> Dict[str, Any]:
        """
        Convert single product to InvenTree format.
        
        Args:
            product_info: Product information to export
            
        Returns:
            Dictionary in InvenTree format
        """
        return product_info.to_inventree_format()
    
    def export_multiple(self, products: List[ProductInfo]) -> List[Dict[str, Any]]:
        """
        Convert multiple products to InvenTree format.
        
        Args:
            products: List of product information to export
            
        Returns:
            List of dictionaries in InvenTree format
        """
        return [self.export_single(product) for product in products]
    
    def save_to_file(self, data: Any, filename: Optional[str] = None) -> Path:
        """
        Save InvenTree-formatted data to JSON file.
        
        Args:
            data: Data to save
            filename: Optional filename
            
        Returns:
            Path to saved file
        """
        import json
        
        if filename is None:
            filename = self.get_default_filename('json')
        
        if self.output_path:
            file_path = self.output_path / filename
        else:
            file_path = Path(filename)
        
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        return file_path
    
    def create_parts_in_inventree(self, products: List[ProductInfo]) -> Dict[str, Any]:
        """
        Create parts directly in InvenTree via API.
        
        Args:
            products: List of products to create
            
        Returns:
            Dictionary with creation results
        """
        if not self.api:
            raise RuntimeError("InvenTree API not initialized")
        
        results = {
            'created': [],
            'failed': [],
            'skipped': []
        }
        
        for product in products:
            try:
                part_data = self.export_single(product)
                
                # Handle category creation if needed
                if self.create_missing_categories and part_data.get('category'):
                    self._ensure_category_exists(part_data['category'])
                
                # Handle supplier creation if needed
                if self.create_missing_suppliers and part_data.get('default_supplier'):
                    self._ensure_supplier_exists(part_data['default_supplier'])
                
                # Create the part
                from inventree.part import Part
                
                # Check if part already exists
                existing_parts = Part.list(
                    self.api, 
                    IPN=part_data.get('IPN'),
                    name=part_data.get('name')
                )
                
                if existing_parts:
                    self.logger.info(f"Part already exists: {part_data.get('name')}")
                    results['skipped'].append({
                        'name': part_data.get('name'),
                        'reason': 'Already exists'
                    })
                    continue
                
                # Create new part
                new_part = Part.create(self.api, part_data)
                results['created'].append({
                    'name': part_data.get('name'),
                    'pk': new_part.pk,
                    'url': product.product_url
                })
                
                self.logger.info(f"Created part: {part_data.get('name')}")
                
            except Exception as e:
                self.logger.error(f"Failed to create part {product.title}: {e}")
                results['failed'].append({
                    'name': product.title,
                    'error': str(e),
                    'url': product.product_url
                })
        
        return results
    
    def _ensure_category_exists(self, category_name: str) -> int:
        """
        Ensure a category exists, create if it doesn't.
        
        Args:
            category_name: Name of the category
            
        Returns:
            Category ID
        """
        from inventree.part import PartCategory
        
        # Check if category exists
        categories = PartCategory.list(self.api, name=category_name)
        
        if categories:
            return categories[0].pk
        
        # Create new category
        new_category = PartCategory.create(self.api, {
            'name': category_name,
            'description': f"Auto-created category for {category_name}"
        })
        
        self.logger.info(f"Created category: {category_name}")
        return new_category.pk
    
    def _ensure_supplier_exists(self, supplier_name: str) -> int:
        """
        Ensure a supplier exists, create if it doesn't.
        
        Args:
            supplier_name: Name of the supplier
            
        Returns:
            Supplier ID
        """
        from inventree.company import Company
        
        # Check if supplier exists
        suppliers = Company.list(self.api, name=supplier_name, is_supplier=True)
        
        if suppliers:
            return suppliers[0].pk
        
        # Create new supplier
        new_supplier = Company.create(self.api, {
            'name': supplier_name,
            'description': f"Auto-created supplier: {supplier_name}",
            'is_supplier': True,
            'is_customer': False
        })
        
        self.logger.info(f"Created supplier: {supplier_name}")
        return new_supplier.pk
