from typing import List, Optional
from datetime import datetime, timedelta
from connect_db import DatabaseConnection

from response.response_message import ResponseMessage
from dialogs.price_unit_dialog.models.price_unit_dialog_models import ProductInPriceUnitModel, PriceUnitTableItemModel

class PriceUnitDialogRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        
    def get_product_by_sku(self, sku: str):
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


    def submit_price_unit(self, price_unit_data: PriceUnitTableItemModel):
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Insert price unit
            sql = '''INSERT INTO units (sku, unit, barcode, unit_value, price) VALUES (?, ?, ?, ?, ?)'''
            
            self.cursor.execute(sql, (price_unit_data.sku, price_unit_data.unit, price_unit_data.barcode, 
                                      price_unit_data.unit_value, price_unit_data.price))
            

            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(
                message="Successfully submitted price unit",
                data=None
            )

        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        

    def update_price_unit(self, price_unit_data: PriceUnitTableItemModel):
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Update price unit
            sql = '''UPDATE units SET barcode = ?, unit_value = ?, price = ? WHERE sku = ? AND unit = ?'''
            
            self.cursor.execute(sql, (price_unit_data.barcode, price_unit_data.unit_value, price_unit_data.price, 
                                      price_unit_data.sku, price_unit_data.unit))
            

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
        try:
            sql = 'DELETE FROM units WHERE sku = ? AND unit = ?'
            self.cursor.execute(sql, (sku, unit))
            
            if self.cursor.rowcount == 0:
                return ResponseMessage.ok(
                    message=f"Price unit with sku {sku} and unit {unit} not found",
                    data=None
                )

            self.db.commit()

            return ResponseMessage.ok(
                message="Successfully deleted price unit",
                data=None
            )
            
        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}")
