import openpyxl
from typing import List

from dialogs.import_products_dialog.repositories.import_products_dialog_repositories import ImportProductsDialogRepository
from dialogs.import_products_dialog.models.import_products_dialog_models import ImportProductsModel
from threads.thread_service import ThreadManager

class ImportProductsDialogService:
    def __init__(self):
        self.repository = ImportProductsDialogRepository()
        self.thread_manager = ThreadManager()


    def import_products(self, file_path: str, on_complete=None, on_error=None, on_progress=None):
        """
        Import an Excel file in a background thread.
        
        Args:
            file_path: Path to the Excel file
            on_complete: Callback for when import completes
            on_error: Callback for when an error occurs
            on_progress: Callback for progress updates
        """
        # Start the import process in a background thread
        self.thread_manager.run_in_thread(
            self.import_excel_task,
            on_complete,
            on_error,
            on_progress,
            file_path               
        )
    

    def import_excel_task(self, file_path):
        """
        Process Excel file in background thread.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            List of processed products or error information
        """
        try:
            workbook = openpyxl.load_workbook(file_path)
            sheet = workbook.active
            
            # Store validation errors
            errors = []
            # Store valid products
            valid_products = []
            
            category_set = set()
            supplier_set = set()

            # Process each row
            total_rows = 0
            for co, row in enumerate(sheet.iter_rows()):
                total_rows = co
                if co == 0:  # Skip header row
                    continue
                
                # Extract values
                sku = row[0].value
                product_name = row[1].value
                barcode = row[2].value
                unit = row[3].value
                cost_price = row[4].value
                price = row[5].value
                stock = row[6].value
                remarks = row[7].value
                category_name = row[8].value
                supplier_name = row[9].value

                # Validate required fields
                if sku is None or product_name is None or unit is None or price is None or stock is None:
                    errors.append({
                        'row': co,
                        'message': f'Error Import For Row {co}, SKU: {sku}, Product Name: {product_name}, Unit: {unit}, Price: {price}, Stock: {stock}',
                        'type': 'missing_fields'
                    })
                    break
                
                # Convert to strings
                sku = str(sku)
                product_name = str(product_name)
                barcode = str(barcode) if barcode is not None else ""
                unit = str(unit)
                cost_price = str(cost_price) if cost_price is not None else "0"
                price = str(price)
                stock = str(stock)
                remarks = str(remarks) if remarks is not None else ""
                category_name = str(category_name) if category_name is not None else ""
                supplier_name = str(supplier_name) if supplier_name is not None else ""

                category_set.add(category_name.upper())
                supplier_set.add(supplier_name.upper())

                # Validate empty strings
                if sku.strip() == '' or product_name.strip() == '' or unit.strip() == '' or price.strip() == '' or stock.strip() == '':
                    errors.append({
                        'row': co,
                        'message': f'Error Import For Row {co}, SKU: {sku}, Product Name: {product_name}, Unit: {unit}, Price: {price}, Stock: {stock}',
                        'type': 'empty_fields'
                    })
                    break
                
                # If we get here, the product is valid
                valid_products.append(ImportProductsModel(
                    sku=sku.strip(),
                    product_name=product_name.strip(),
                    barcode=barcode.strip(),
                    unit=unit.strip(),
                    cost_price=cost_price.strip(),
                    price=price.strip(),
                    stock=stock.strip(),
                    remarks=remarks.strip(),
                    category=category_name.strip().upper(),
                    supplier=supplier_name.strip().upper()
                ))
                
            # Return the results
            result = {
                'valid_products': valid_products,
                'category_set': category_set,
                'supplier_set': supplier_set,
                'errors': errors,
                'total_rows': total_rows,
                'valid_count': len(valid_products),
                'error_count': len(errors)
            }
            
            return result
            
        except Exception as e:
            print(f"ImportProductsDialogService: Error processing Excel file: {str(e)}")
            # Re-raise the exception to be caught by the worker
            raise
    

    def import_products_to_database(self, products: List[ImportProductsModel], category_set: set, supplier_set: set, 
                                    on_complete=None, on_error=None, on_progress=None):
        batch_size = 250
        if len(products) <= 100:
            batch_size = 25
        elif len(products) <= 500:
            batch_size = 50

        self.thread_manager.run_in_thread(
            self.repository.import_products_to_database,
            on_complete,
            on_error,
            on_progress,
            products,
            batch_size,
            category_set,
            supplier_set
        )