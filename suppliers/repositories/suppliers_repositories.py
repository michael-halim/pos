from typing import List, Optional
from datetime import datetime, timedelta
from connect_db import DatabaseConnection
from ..models.suppliers_models import SuppliersModel
from response.response_message import ResponseMessage


class SuppliersRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        

    def get_suppliers(self, search_text: str = None):
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
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Insert master stock
            sql = '''INSERT INTO suppliers (supplier_name, supplier_address, supplier_phone, 
                                            supplier_city, supplier_remarks) 
                    VALUES (?, ?, ?, ?, ?)'''
            
            self.cursor.execute(sql, (supplier_data.supplier_name, supplier_data.supplier_address, 
                                      supplier_data.supplier_phone, supplier_data.supplier_city, 
                                      supplier_data.supplier_remarks))
            
            # Commit Transaction
            self.db.commit()
            
            return ResponseMessage.ok(message="Supplier submitted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to submit supplier: {str(e)}")
        

    def update_supplier(self, supplier_data: SuppliersModel):
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Update master stock
            sql = '''UPDATE suppliers 
                    SET supplier_address = ?, supplier_phone = ?, 
                        supplier_city = ?, supplier_remarks = ? 
                    WHERE supplier_id = ?'''
            
            self.cursor.execute(sql, (supplier_data.supplier_address, supplier_data.supplier_phone, 
                                      supplier_data.supplier_city, supplier_data.supplier_remarks, 
                                      supplier_data.supplier_id))

            # Commit Transaction  
            self.db.commit()

            return ResponseMessage.ok(message="Supplier updated successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to update supplier: {str(e)}")


    def delete_supplier_by_id(self, supplier_id: int):
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Delete supplier
            sql = '''DELETE FROM suppliers WHERE supplier_id = ?'''
            self.cursor.execute(sql, (supplier_id,))

            # Commit Transaction  
            self.db.commit()

            return ResponseMessage.ok(message="Supplier deleted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to delete supplier: {str(e)}")    