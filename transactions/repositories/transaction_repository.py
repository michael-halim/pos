from typing import List


# Import Models
from ..models.transactions_models import ProductModel, TransactionModel, DetailTransactionModel, ProductUnitDetailModel
from ..models.transactions_models import PendingTransactionModel, PendingDetailTransactionModel, PendingDetailTransactionToTransactionModel


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
            total_amount = transaction.total_amount
            payment_method = transaction.payment_method
            payment_rp = transaction.payment_amount
            payment_change = transaction.payment_change
            payment_remarks = transaction.payment_remarks
            
            self.cursor.execute(sql, (transaction_id, total_amount, payment_method, 
                                      payment_rp, payment_change, current_time, payment_remarks))
            

            # Insert all detail transactions
            sql = '''INSERT INTO detail_transactions 
                    (transaction_id, sku, unit, unit_value, qty, price, discount, sub_total) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
                

            for detail in detail_transactions:  
                transaction_id = detail.transaction_id
                sku = detail.sku
                unit = detail.unit
                unit_value = detail.unit_value
                qty = detail.qty
                price = detail.price
                discount_rp = detail.discount_rp
                subtotal = detail.subtotal
                
                # Insert detail transaction
                self.cursor.execute(sql, (transaction_id, sku, unit, unit_value, 
                                          qty, price, discount_rp, subtotal))
                
                # Update product stock
                update_sql = 'UPDATE products SET stock = stock - ? WHERE sku = ? AND unit = ?'
                self.cursor.execute(update_sql, (qty, sku, unit))

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
        
    def create_pending_transaction(self, pending_transaction: PendingTransactionModel, pending_detail_transactions: List[PendingDetailTransactionModel]):
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get current timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert main transaction first
            sql = '''INSERT INTO pending_transactions (transaction_id, total_amount, discount_transaction_id, discount_amount, created_at, payment_remarks) 
                    VALUES (?, ?, ?, ?, ?, ?)'''
            
            transaction_id = pending_transaction.transaction_id
            total_amount = pending_transaction.total_amount
            discount_transaction_id = pending_transaction.discount_transaction_id
            discount_amount = pending_transaction.discount_amount
            payment_remarks = pending_transaction.payment_remarks

            self.cursor.execute(sql, (transaction_id, total_amount, discount_transaction_id, discount_amount, current_time, payment_remarks))
            
            # Insert all detail transactions
            sql = '''INSERT INTO pending_detail_transactions 

                    (transaction_id, sku, unit, unit_value, qty, price, discount, sub_total) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
                

            for detail in pending_detail_transactions:
                transaction_id = detail.transaction_id
                sku = detail.sku
                unit = detail.unit
                unit_value = detail.unit_value
                qty = detail.qty
                price = detail.price
                discount_rp = detail.discount
                subtotal = detail.subtotal
                
                # Insert detail transaction
                self.cursor.execute(sql, (transaction_id, sku, unit, unit_value, 
                                          qty, price, discount_rp, subtotal))
                

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
                    PendingDetailTransactionToTransactionModel(
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
        sql = '''SELECT u.unit, u.unit_value, p.price, p.stock 
                    FROM products p 
                    LEFT JOIN units u ON p.sku = u.sku and p.unit = u.unit
                    WHERE p.sku = ?'''

        self.cursor.execute(sql, (sku,))
        results =  self.cursor.fetchall()

        product_unit_details = [
            ProductUnitDetailModel(unit=r[0], unit_value=r[1], price=r[2], stock=r[3]) 
            for r in results
        ]

        return product_unit_details
    
    def get_product_by_sku(self, sku: str) -> ProductModel:
        sql = 'SELECT product_name, price, stock FROM products WHERE sku = ?'
        self.cursor.execute(sql, (sku,))
        result = self.cursor.fetchone()

        return ProductModel(product_name=result[0], price=result[1], stock=result[2])
