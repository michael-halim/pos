from connect_db import DatabaseConnection
from datetime import datetime
import json

from dialogs.price_unit_dialog.models.price_unit_dialog_models import ProductInPriceUnitModel, PriceUnitTableItemModel, PriceUnitsModel

from response.response_message import ResponseMessage
from generals.constants import (
    PERM_C_PRODUCTS, PERM_U_PRODUCTS, PERM_D_PRODUCTS
)
from generals.messages import (
    ERR_PERM_C_PRODUCTS, ERR_PERM_U_PRODUCTS, ERR_PERM_D_PRODUCTS
)
from generals.permission_manager import PermissionManager


class PriceUnitDialogRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()


    def get_product_by_sku(self, sku: str):
        if not self.permission_manager.has_permission(PERM_C_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_C_PRODUCTS)

        try:

            sql = 'SELECT product_name, unit, price FROM products WHERE sku = ? LIMIT 1'
            self.cursor.execute(sql, (sku,))

            if self.cursor.rowcount == 0:
                return ResponseMessage.ok(
                    message=f"Product with sku {sku} not found",
                    data=None
                )

            result = self.cursor.fetchone()
            if result:
                return ResponseMessage.ok(
                    message="Success",
                    data=ProductInPriceUnitModel(
                            product_name=result[0], 
                            barcode='barcode', 
                            unit=result[1], 
                            price=result[2], 
                        )
                    )
            
            return ResponseMessage.ok(
                message="Success",
                data=None
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def get_product_units_by_sku(self, sku: str):
        try:
            sql = 'SELECT unit, barcode, unit_value, price FROM units WHERE sku = ?'
            self.cursor.execute(sql, (sku,))

            if self.cursor.rowcount == 0:
                return ResponseMessage.ok(
                    message=f"Product with sku {sku} not found",
                    data=None
                )

            unit_results = self.cursor.fetchall()
            if unit_results:
                price_unit_table_items = [
                    PriceUnitTableItemModel(
                        unit=ur[0], 
                        barcode=ur[1], 
                        unit_value=ur[2], 
                        price=ur[3]
                    ) for ur in unit_results
                ]

                return ResponseMessage.ok(
                    message="Successfully fetched product units",
                    data=price_unit_table_items
                )
            
            return ResponseMessage.ok(
                message="Success with no data",
                data=None
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def submit_price_unit(self, price_unit_data: PriceUnitsModel):
        if not self.permission_manager.has_permission(PERM_C_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_C_PRODUCTS)

        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Check price unit
            check_price_unit_result = self.check_price_unit(price_unit_data.sku, price_unit_data.unit, price_unit_data.unit_value)
            if not check_price_unit_result.success:
                return check_price_unit_result

            # Insert price unit
            sql = '''INSERT INTO units (sku, unit, barcode, unit_value, price) VALUES (?, ?, ?, ?, ?)'''
            
            self.cursor.execute(sql, (price_unit_data.sku, price_unit_data.unit, price_unit_data.barcode, 
                                      price_unit_data.unit_value, price_unit_data.price))
            
            # Insert Log
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_data = {    
                'sku': price_unit_data.sku, 
                'unit': price_unit_data.unit, 
                'barcode': price_unit_data.barcode, 
                'unit_value': price_unit_data.unit_value, 
                'price': price_unit_data.price
            }

            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            self.cursor.execute(sql, (f'Price Unit {price_unit_data.unit} created', f'Price Unit {price_unit_data.unit} created successfully!', 'C', 
                                        None, json.dumps(new_data), today, self.permission_manager.get_user_id()))

            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(
                message="Successfully submitted price unit",
                data=None
            )

        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        

    def update_price_unit(self, price_unit_data: PriceUnitsModel):
        if not self.permission_manager.has_permission(PERM_U_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_U_PRODUCTS)

        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')
            
            # Check price unit
            check_price_unit_result = self.check_price_unit(price_unit_data.sku, price_unit_data.unit, price_unit_data.unit_value)
            if not check_price_unit_result.success:
                return check_price_unit_result
            
            # Get price unit data
            sql = 'SELECT sku, barcode, unit, unit_value, price FROM units WHERE sku = ? AND unit = ? LIMIT 1'
            self.cursor.execute(sql, (price_unit_data.sku, price_unit_data.unit))

            price_unit_data = self.cursor.fetchone()
            old_data = {}
            if price_unit_data:
                old_data = {
                    'sku': price_unit_data[0],
                    'barcode': price_unit_data[1],
                    'unit': price_unit_data[2],
                    'unit_value': price_unit_data[3],
                    'price': price_unit_data[4]
                }

            new_data = {
                'sku': price_unit_data.sku,
                'unit': price_unit_data.unit,
                'barcode': price_unit_data.barcode,
                'unit_value': price_unit_data.unit_value,
                'price': price_unit_data.price
            }

            # Update price unit
            sql = '''UPDATE units SET barcode = ?, unit_value = ?, price = ? WHERE sku = ? AND unit = ?'''
            self.cursor.execute(sql, (price_unit_data.barcode, price_unit_data.unit_value, price_unit_data.price, 
                                      price_unit_data.sku, price_unit_data.unit))
            

            # Insert Log
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            self.cursor.execute(sql, (f'Price Unit {price_unit_data.unit} updated', f'Price Unit {price_unit_data.unit} updated successfully!', 'U', 
                                        json.dumps(old_data), json.dumps(new_data), today, self.permission_manager.get_user_id()))


            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(
                message="Successfully updated price unit",
                data=None
            )

        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def delete_price_unit_by_sku_and_unit(self, sku: str, unit: str):
        if not self.permission_manager.has_permission(PERM_D_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_D_PRODUCTS)

        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get price unit data
            sql = 'SELECT sku, barcode, unit, unit_value, price FROM units WHERE sku = ? AND unit = ? LIMIT 1'
            self.cursor.execute(sql, (sku, unit))

            price_unit_data = self.cursor.fetchone()
            old_data = {}
            if price_unit_data:
                old_data = {
                    'sku': price_unit_data[0],
                    'barcode': price_unit_data[1],
                    'unit': price_unit_data[2],
                    'unit_value': price_unit_data[3],
                    'price': price_unit_data[4]
                }


            # Delete price unit
            sql = 'DELETE FROM units WHERE sku = ? AND unit = ?'
            self.cursor.execute(sql, (sku, unit))
            
            if self.cursor.rowcount == 0:
                return ResponseMessage.ok(
                    message=f"Price unit with sku {sku} and unit {unit} not found",
                    data=None
                )


            # Insert Log
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            self.cursor.execute(sql, (f'Price Unit {unit} deleted', f'Price Unit {unit} deleted successfully!', 'D', 
                                        json.dumps(old_data), None, today, self.permission_manager.get_user_id()))


            # Commit transaction
            self.db.commit()

            return ResponseMessage.ok(
                message="Successfully deleted price unit",
                data=None
            )
            
        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def check_price_unit(self, sku: str, unit: str, unit_value: int):
        try:
            # Check if price unit already exists
            sql = 'SELECT COUNT(*) FROM units WHERE sku = ? AND unit = ?'
            self.cursor.execute(sql, (sku, unit))

            if self.cursor.fetchone()[0] > 0:
                return ResponseMessage.fail(message='Price unit already exists')

            # Check if price unit < 1
            if int(unit_value) < 1:
                return ResponseMessage.fail(message='Unit value cannot be less than 1')

            return ResponseMessage.ok(
                message="Successfully checked price unit",
                data=None
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
