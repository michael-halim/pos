from connect_db import DatabaseConnection

from response.response_message import ResponseMessage
from ..models.suppliers_dialog_models import SupplierModel

class SuppliersDialogRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        
    
    def get_suppliers(self, search_text: str = ''):
        try:
            suppliers_result = []
            if search_text:
                sql = '''SELECT supplier_id, supplier_name, supplier_address, supplier_city, supplier_phone, supplier_remarks 
                            FROM suppliers
                            WHERE supplier_id LIKE ? OR supplier_name LIKE ? OR supplier_address LIKE ? OR supplier_city LIKE ? OR supplier_phone LIKE ? OR supplier_remarks LIKE ?'''
                
                search_text = f'%{search_text}%'
                suppliers_result = self.cursor.execute(sql, (search_text, search_text, search_text, search_text, search_text, search_text))
            else:
                sql = '''SELECT supplier_id, supplier_name, supplier_address, supplier_city, supplier_phone, supplier_remarks 
                            FROM suppliers'''

                suppliers_result = self.cursor.execute(sql)

            suppliers = [
                SupplierModel(supplier_id=r[0], supplier_name=r[1], supplier_address=r[2], supplier_city=r[3], supplier_phone=r[4], supplier_remarks=r[5]) 
                for r in suppliers_result
            ]

            return ResponseMessage.ok(
                message="Suppliers fetched successfully!",
                data=suppliers
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")

