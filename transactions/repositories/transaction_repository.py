from typing import List


# Import Models
from ..models.transactions_models import ProductModel, TransactionModel, DetailTransactionModel, ProductUnitDetailModel
from ..models.transactions_models import PendingTransactionModel, TransactionTableItemModel


from connect_db import DatabaseConnection
from datetime import datetime, timedelta
from ..models.result import ResponseMessage



class TransactionRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
    
    def submit_transaction(self, transaction: TransactionModel, detail_transactions: List[DetailTransactionModel]) -> ResponseMessage:
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get current timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert main transaction first
            sql = '''INSERT INTO transactions (transaction_id, total_amount, payment_method, 
                                            payment_rp, payment_change, created_at, payment_remarks) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            
            transaction_id = transaction.transaction_id
            self.cursor.execute(sql, (transaction_id, transaction.total_amount, transaction.payment_method, 
                                      transaction.payment_amount, transaction.payment_change, current_time, transaction.payment_remarks))
            

            # Insert all detail transactions
            sql = '''INSERT INTO detail_transactions 
                    (transaction_id, sku, unit, unit_value, qty, price, discount, sub_total) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
                

            for detail in detail_transactions:  
                sku = detail.sku
                qty = detail.qty
                unit_value = detail.unit_value
                unit = detail.unit
                stock_affected: int = int(qty) * int(unit_value)
                # Insert detail transaction
                self.cursor.execute(sql, (detail.transaction_id, sku, unit, unit_value, 
                                          qty, detail.price,  detail.discount, detail.subtotal))
                
                # Update product stock
                update_sql = 'UPDATE products SET stock = stock - ? WHERE sku = ?'
                self.cursor.execute(update_sql, (stock_affected, sku))

            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(f"Transaction#{transaction_id} submitted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(f"Failed to submit transaction: {str(e)}")


    def create_transaction_id(self, is_pending: bool = False) -> str:
        # Get Today's Date
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        # Get count of all transactions today   
        sql = '''SELECT COUNT(*) FROM transactions WHERE created_at >= ? and created_at < ?'''
        self.cursor.execute(sql, (f'{today}', f'{tomorrow}'))

        transaction_count_today = self.cursor.fetchone()[0]
        transaction_count_today += 1

        if is_pending:
            return f'P{datetime.now().strftime("%Y%m%d")}{transaction_count_today:04d}'

        return f'A{datetime.now().strftime("%Y%m%d")}{transaction_count_today:04d}'
        
    def create_pending_transaction(self, pending_transaction: PendingTransactionModel, detail_transactions: List[DetailTransactionModel]):
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get current timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert main transaction first
            sql = '''INSERT INTO pending_transactions (transaction_id, total_amount, discount_transaction_id, discount_amount, created_at, payment_remarks) 
                    VALUES (?, ?, ?, ?, ?, ?)'''
            
            self.cursor.execute(sql, (pending_transaction.transaction_id,  pending_transaction.total_amount, 
                                      pending_transaction.discount_transaction_id, pending_transaction.discount_amount, 
                                      current_time, pending_transaction.payment_remarks))
            
            # Insert all detail transactions
            sql = '''INSERT INTO pending_detail_transactions 

                    (transaction_id, sku, unit, unit_value, qty, price, discount, sub_total) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
                

            for detail in detail_transactions:
                # Insert detail transaction
                self.cursor.execute(sql, (detail.transaction_id,  detail.sku, detail.unit, 
                                          detail.unit_value, detail.qty, detail.price, detail.discount, 
                                          detail.subtotal))
                

            # If everything successful, commit the transaction
            self.db.commit()

            return ResponseMessage.ok("Transaction pending successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()

            return ResponseMessage.fail(f"Failed to create pending transaction: {str(e)}")

    def get_pending_transactions_by_transaction_id(self, transaction_id: str):
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            sql = '''SELECT pdt.sku, p.product_name, pdt.price, pdt.qty, pdt.unit, pdt.unit_value, pdt.discount, pdt.sub_total 
                    FROM pending_detail_transactions pdt
                    JOIN products p ON p.sku = pdt.sku and p.unit = pdt.unit
                    WHERE pdt.transaction_id = ?'''
            
            self.cursor.execute(sql, (transaction_id,))

            results = self.cursor.fetchall()

            # Delete pending detail transactions
            sql = '''DELETE FROM pending_detail_transactions WHERE transaction_id = ?'''

            self.cursor.execute(sql, (transaction_id,))

            # Delete pending transactions
            sql = '''DELETE FROM pending_transactions WHERE transaction_id = ?'''

            self.cursor.execute(sql, (transaction_id,))

            self.db.commit()

            pending_detail_transactions = []
            for r in results:
                pending_detail_transactions.append(
                    TransactionTableItemModel(
                        sku=r[0], product_name=r[1],
                        price=r[2],qty=r[3],
                        unit=r[4],unit_value=r[5],
                        discount=r[6], subtotal=r[7]
                    )
                )

            return {
                'message': ResponseMessage.ok("Transaction pending successfully!"),
                'data': pending_detail_transactions
            }

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()

            return {
                'message': ResponseMessage.fail(f"Failed to add transaction: {str(e)}"),
                'data': []
            }

    def get_product_unit_details(self, sku: str) -> list[ProductUnitDetailModel]:
        sql = '''SELECT u.unit, u.unit_value, u.price 
                    FROM units u
                    WHERE u.sku = ?'''

        self.cursor.execute(sql, (sku,))
        results =  self.cursor.fetchall()

        if results:
            product_unit_details = [
                ProductUnitDetailModel(unit=r[0], unit_value=r[1], price=r[2]) 
                for r in results
            ]
            return product_unit_details

        return []
    
    def get_product_by_sku(self, sku: str):
        try:
            sql = 'SELECT product_name, price, unit, stock FROM products WHERE sku = ?'
            self.cursor.execute(sql, (sku,))

            if self.cursor.rowcount == 0:
                return {
                    'success': True,
                    'message': f"Product with sku {sku} not found",
                    'data': None
                }

            result = self.cursor.fetchone()
            return {
                'success': True,
                'message': "Success",
                'data': ProductModel(product_name=result[0], price=result[1], unit=result[2], stock=result[3])
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"Error: {str(e)}",
                'data': None
            }

