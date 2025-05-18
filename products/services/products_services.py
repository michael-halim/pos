from products.repositories.products_repositories import ProductsRepository

from openpyxl import Workbook

from generals.permission_manager import PermissionManager
from generals.constants import PERM_R_PRODUCTS, PERM_D_PRODUCTS, PERM_E_PRODUCTS
from generals.messages import ERR_PERM_R_PRODUCTS, ERR_PERM_D_PRODUCTS, ERR_PERM_E_PRODUCTS
from products.models.products_models import ProductsExportModel

from response.response_message import ResponseMessage
from exports.export_service import ExportService
from threads.thread_service import ThreadManager


class ProductsService:
    def __init__(self):
        self.repository = ProductsRepository()
        self.permission_manager = PermissionManager()
        self.thread_manager = ThreadManager()
        self.export_service = ExportService()


    def get_products(self, search_text: str = None, limit: int = 100, offset: int = 50):
        if not self.permission_manager.has_permission(PERM_R_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_R_PRODUCTS)
        
        return self.repository.get_products(search_text, limit, offset)


    def get_products_for_export(self, limit: int = 1000):
        if not self.permission_manager.has_permission(PERM_E_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_E_PRODUCTS)

        return self.repository.get_products_for_export(limit)


    def delete_products_by_sku(self, sku: str):
        if not self.permission_manager.has_permission(PERM_D_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_D_PRODUCTS)
        
        return self.repository.delete_products_by_sku(sku)


    def export_excel(self, data: list[ProductsExportModel], file_path: str, on_complete=None, on_error=None, on_progress=None):
        if not self.permission_manager.has_permission(PERM_E_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_E_PRODUCTS)

        self.thread_manager.run_in_thread(
            self.export_excel_task,
            on_complete,
            on_error, on_progress, data, file_path)
        

    def export_excel_task(self, data: list[ProductsExportModel], file_path: str):
        # Create workbook
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Products"

        # Add headers
        headers = ['SKU', 'Product Name', 'Barcode', 'Unit', 'Cost Price', 'Price', 'Stock', 'Remarks']
        worksheet.append(headers)

        # Add data
        for product in data:    
            worksheet.append([product.sku, product.product_name, product.barcode, product.unit, product.cost_price, product.price, product.stock, product.remarks])

        # Save workbook
        workbook.save(file_path)

        return ResponseMessage.ok(message=f"Products exported successfully to:\n{file_path}")