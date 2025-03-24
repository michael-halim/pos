from connect_db import DatabaseConnection
from datetime import datetime
import json 

from suppliers.models.suppliers_models import SuppliersModel

from response.response_message import ResponseMessage
from generals.permission_manager import PermissionManager
from generals.constants import (
    PERM_R_SUPPLIERS, PERM_C_SUPPLIERS, PERM_U_SUPPLIERS, PERM_D_SUPPLIERS
)
from generals.messages import (
    ERR_PERM_R_SUPPLIERS, ERR_PERM_C_SUPPLIERS, ERR_PERM_U_SUPPLIERS, ERR_PERM_D_SUPPLIERS
)

class SuppliersRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()
        

    def get_suppliers(self, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_SUPPLIERS):
            return ResponseMessage.fail(message=ERR_PERM_R_SUPPLIERS)

        try:
            suppliers_result = []
            if search_text:
                sql = '''SELECT supplier_id, supplier_name, supplier_address, supplier_phone, supplier_city, supplier_remarks 
                            FROM suppliers 
                            WHERE supplier_name LIKE ? OR supplier_address LIKE ? OR supplier_phone LIKE ? OR supplier_city LIKE ? OR supplier_remarks LIKE ?'''
                
                search_text = f'%{search_text}%'
                suppliers_result = self.cursor.execute(sql, (search_text, search_text, search_text, search_text, search_text))

            else:
                sql = '''SELECT supplier_id, supplier_name, supplier_address, supplier_phone, supplier_city, supplier_remarks 
                            FROM suppliers '''
                
                suppliers_result = self.cursor.execute(sql)

            suppliers = [
                SuppliersModel(supplier_id=p[0], supplier_name=p[1], supplier_address=p[2], 
                                    supplier_phone=p[3], supplier_city=p[4], supplier_remarks=p[5]) 
                for p in suppliers_result
            ]

            return ResponseMessage.ok(
                message="Products fetched successfully!",
                data=suppliers
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def get_supplier_by_id(self, supplier_id: int):
        if not self.permission_manager.has_permission(PERM_R_SUPPLIERS):
            return ResponseMessage.fail(message=ERR_PERM_R_SUPPLIERS)

        try: 
            sql = '''SELECT supplier_id, supplier_name, supplier_address, supplier_phone, 
                            supplier_city, supplier_remarks 
                    FROM suppliers 
                    WHERE supplier_id = ?
                    LIMIT 1'''
            
            supplier_result = self.cursor.execute(sql, (supplier_id,))
            supplier = supplier_result.fetchone()

            if not supplier:
                return ResponseMessage.fail(message="Supplier not found!")

            supplier = SuppliersModel(supplier_id=supplier[0], supplier_name=supplier[1], supplier_address=supplier[2], 
                                    supplier_phone=supplier[3], supplier_city=supplier[4], supplier_remarks=supplier[5]) 
            
            return ResponseMessage.ok(
                message="Supplier fetched successfully!",
                data=supplier
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
    

    def submit_supplier(self, supplier_data: SuppliersModel):
        if not self.permission_manager.has_permission(PERM_C_SUPPLIERS):
            return ResponseMessage.fail(message=ERR_PERM_C_SUPPLIERS)

        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get old supplier data
            sql = '''SELECT supplier_id, supplier_name, supplier_address, supplier_phone, 
                            supplier_city, supplier_remarks 
                    FROM suppliers 
                    WHERE supplier_id = ?
                    LIMIT 1'''
            self.cursor.execute(sql, (supplier_data.supplier_id,))
            result = self.cursor.fetchone()
            old_data = {
                'supplier_id': result[0],
                'supplier_name': result[1],
                'supplier_address': result[2],
                'supplier_phone': result[3],
                'supplier_city': result[4],
                'supplier_remarks': result[5]
            
            }
            
            # Insert master stock
            sql = '''INSERT INTO suppliers (supplier_name, supplier_address, supplier_phone, 
                                            supplier_city, supplier_remarks) 
                    VALUES (?, ?, ?, ?, ?)'''
            
            self.cursor.execute(sql, (supplier_data.supplier_name, supplier_data.supplier_address, 
                                      supplier_data.supplier_phone, supplier_data.supplier_city, 
                                      supplier_data.supplier_remarks))
            
            # Insert Log
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_data = {    
                'supplier_id': supplier_data.supplier_id,
                'supplier_name': supplier_data.supplier_name,
                'supplier_address': supplier_data.supplier_address,
                'supplier_phone': supplier_data.supplier_phone,
                'supplier_city': supplier_data.supplier_city,
                'supplier_remarks': supplier_data.supplier_remarks
            }
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            self.cursor.execute(sql, (f'Supplier {supplier_data.supplier_name} created', f'Supplier {supplier_data.supplier_name} created successfully!', 'C', 
                                        json.dumps(old_data), json.dumps(new_data), today, self.permission_manager.get_user_id()))

            # Commit Transaction
            self.db.commit()
            
            return ResponseMessage.ok(message="Supplier submitted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to submit supplier: {str(e)}")
        

    def update_supplier(self, supplier_data: SuppliersModel):
        if not self.permission_manager.has_permission(PERM_U_SUPPLIERS):
            return ResponseMessage.fail(message=ERR_PERM_U_SUPPLIERS)

        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get old supplier data
            sql = '''SELECT supplier_id, supplier_name, supplier_address, supplier_phone, 
                            supplier_city, supplier_remarks 
                    FROM suppliers 
                    WHERE supplier_id = ?
                    LIMIT 1'''
            self.cursor.execute(sql, (supplier_data.supplier_id,))
            result = self.cursor.fetchone()
            old_data = {
                'supplier_id': result[0],
                'supplier_name': result[1],
                'supplier_address': result[2],
                'supplier_phone': result[3],
                'supplier_city': result[4],
                'supplier_remarks': result[5]
            }

            # Update master stock
            sql = '''UPDATE suppliers 
                    SET supplier_address = ?, supplier_phone = ?, 
                        supplier_city = ?, supplier_remarks = ? 
                    WHERE supplier_id = ?'''
            
            self.cursor.execute(sql, (supplier_data.supplier_address, supplier_data.supplier_phone, 
                                      supplier_data.supplier_city, supplier_data.supplier_remarks, 
                                      supplier_data.supplier_id))

            # Insert Log
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_data = {
                'supplier_id': supplier_data.supplier_id,
                'supplier_name': supplier_data.supplier_name,
                'supplier_address': supplier_data.supplier_address, 
                'supplier_phone': supplier_data.supplier_phone,
                'supplier_city': supplier_data.supplier_city,
                'supplier_remarks': supplier_data.supplier_remarks
            }
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            self.cursor.execute(sql, (f'Supplier {supplier_data.supplier_name} updated', f'Supplier {supplier_data.supplier_name} updated successfully!', 'U', 
                                        json.dumps(old_data), json.dumps(new_data), today, self.permission_manager.get_user_id()))


            # Commit Transaction  
            self.db.commit()

            return ResponseMessage.ok(message="Supplier updated successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to update supplier: {str(e)}")


    def delete_supplier_by_id(self, supplier_id: int):
        if not self.permission_manager.has_permission(PERM_D_SUPPLIERS):
            return ResponseMessage.fail(message=ERR_PERM_D_SUPPLIERS)

        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get old supplier data
            sql = '''SELECT supplier_id, supplier_name, supplier_address, supplier_phone, 
                            supplier_city, supplier_remarks 
                    FROM suppliers 
                    WHERE supplier_id = ?
                    LIMIT 1'''
            self.cursor.execute(sql, (supplier_id,))
            result = self.cursor.fetchone()
            old_data = {
                'supplier_id': result[0],
                'supplier_name': result[1],
                'supplier_address': result[2],
                'supplier_phone': result[3],
                'supplier_city': result[4],
                'supplier_remarks': result[5]
            }

            # Delete supplier
            sql = '''DELETE FROM suppliers WHERE supplier_id = ?'''
            self.cursor.execute(sql, (supplier_id,))

            # Insert Log
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            self.cursor.execute(sql, (f'Supplier {result[1]} deleted', f'Supplier {result[1]} deleted successfully!', 'D', 
                                        json.dumps(old_data), None, today, self.permission_manager.get_user_id()))
            # Commit Transaction  
            self.db.commit()

            return ResponseMessage.ok(message="Supplier deleted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to delete supplier: {str(e)}")    