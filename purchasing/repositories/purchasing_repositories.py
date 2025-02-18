from typing import List
from datetime import datetime, timedelta
from connect_db import DatabaseConnection

from ..models.purchasing_models import ProductModel, ProductUnitsModel, PurchasingModel, DetailPurchasingModel, PurchasingHistoryTableItemModel
from dialogs.suppliers_dialog.models.suppliers_dialog_models import SupplierModel

from response.response_message import ResponseMessage

class PurchasingRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()

        
    def get_product_by_sku(self, sku: str):
        try:
            sql = 'SELECT product_name, price, unit, stock FROM products WHERE sku = ?'
            self.cursor.execute(sql, (sku,))

            if self.cursor.rowcount == 0:
                return ResponseMessage.ok(
                    message=f"Product with sku {sku} not found",
                    data=None
                )

            result = self.cursor.fetchone()
            return ResponseMessage.ok(
                message="Success",
                data=ProductModel(product_name=result[0], price=result[1], unit=result[2], stock=result[3])
            )

        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        

    def get_product_unit_details(self, sku: str) -> list[ProductUnitsModel]:
        try:
            sql = '''SELECT u.unit, u.unit_value FROM units u WHERE u.sku = ?'''

            self.cursor.execute(sql, (sku,))
            results =  self.cursor.fetchall()

            if self.cursor.rowcount == 0:
                return ResponseMessage.ok(
                    message=f"Product with sku {sku} not found",
                    data=None
                )

            product_units = [
                ProductUnitsModel(unit=r[0], unit_value=r[1])  for r in results
            ]

            return ResponseMessage.ok(
                message="Success",
                data=product_units
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def create_purchasing_id(self) -> str:
        # Get Today's Date
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        # Get count of all transactions today   
        sql = '''SELECT COUNT(*) FROM purchasing_history WHERE created_at >= ? and created_at < ?'''
        self.cursor.execute(sql, (f'{today}', f'{tomorrow}'))

        purchasing_count_today = self.cursor.fetchone()[0]
        purchasing_count_today += 1

        return f'PO{datetime.now().strftime("%Y%m%d")}{purchasing_count_today:04d}'
    

    def submit_purchasing(self, purchasing: PurchasingModel, detail_purchasing: List[DetailPurchasingModel]) -> ResponseMessage:
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get current timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert main purchasing first
            sql = '''INSERT INTO purchasing_history (purchasing_id, supplier_id, invoice_date, invoice_number, 
                                                    invoice_expired_date, total_amount, created_at, purchasing_remarks) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
            
            purchasing_id = purchasing.purchasing_id
            self.cursor.execute(sql, (purchasing_id, purchasing.supplier_id, purchasing.invoice_date, purchasing.invoice_number, 
                                      purchasing.invoice_expired_date, purchasing.total_amount, current_time, purchasing.purchasing_remarks))
            

            # Insert all detail purchasing
            sql = '''INSERT INTO detail_purchasing_history (purchasing_id, sku, unit, qty, price, 
                                                                discount_rp, discount_pct, subtotal) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''

            for detail in detail_purchasing:  
                sku = detail.sku
                qty = detail.qty
                unit_value = detail.unit_value
                unit = detail.unit
                stock_affected: int = int(qty) * int(unit_value)
                # Insert detail purchasing
                self.cursor.execute(sql, (detail.purchasing_id, sku, unit, qty, detail.price,  
                                          detail.discount_rp, detail.discount_pct, detail.subtotal))
                
                # Update product stock, average price, and last price
                # Average Price = ((Average Price * Old Stock) + (New Price * New Qty)) / (Old Stock + New Qty)
                update_sql = '''UPDATE products 
                                SET stock = stock + ?, 
                                    last_price = ?, 
                                    average_price = ((average_price * stock) + ( ? * ? )) / (stock + ?) 
                                WHERE sku = ?'''
                self.cursor.execute(update_sql, (stock_affected, detail.price, detail.price, stock_affected, stock_affected, sku))

            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(f"Purchasing#{purchasing_id} submitted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(f"Failed to submit purchasing: {str(e)}")
        

    def get_supplier_by_id(self, supplier_id: str):
        try:
            sql = '''SELECT supplier_id, supplier_name, supplier_address, supplier_city, 
                            supplier_phone, supplier_remarks 
                     FROM suppliers 
                     WHERE supplier_id = ? 
                     LIMIT 1'''
            
            self.cursor.execute(sql, (supplier_id,))
            result = self.cursor.fetchone()
            
            if result:
                supplier = SupplierModel(
                    supplier_id=result[0],
                    supplier_name=result[1],
                    supplier_address=result[2],
                    supplier_city=result[3],
                    supplier_phone=result[4],
                    supplier_remarks=result[5]
                )

                return ResponseMessage.ok(
                    message="Supplier fetched successfully!",
                    data=supplier
                )
            
            return ResponseMessage.ok(
                message="Supplier not found!",
                data=None
            )
            
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        

    def get_purchasing_history_by_sku(self, sku: str) -> list[PurchasingHistoryTableItemModel]:
        try:
            sql = '''SELECT ph.created_at, s.supplier_name, dph.qty, dph.unit, dph.price, dph.subtotal
                    FROM detail_purchasing_history dph 
                    JOIN purchasing_history ph on ph.purchasing_id = dph.purchasing_id
                    LEFT JOIN suppliers s on s.supplier_id = ph.supplier_id
                    WHERE dph.sku = ?
                    ORDER BY ph.created_at DESC'''
            
            self.cursor.execute(sql, (sku,))

            purchasing_history_results = self.cursor.fetchall()

            if purchasing_history_results:
                purchasing_history = [
                    PurchasingHistoryTableItemModel(created_at=ph[0], 
                                                    supplier_name=ph[1], 
                                                    qty=ph[2], 
                                                    unit=ph[3], 
                                                    price=ph[4], 
                                                    subtotal=ph[5]) 
                    for ph in purchasing_history_results
                ]

                return ResponseMessage.ok(
                    message="Purchasing history fetched successfully!",
                    data=purchasing_history
                )
            
            return ResponseMessage.ok(
                message="Purchasing history not found!",
                data=None
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")