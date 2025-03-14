from connect_db import DatabaseConnection
from datetime import datetime, timedelta
from typing import List

from transactions.models.transactions_models import (
    ProductModel, TransactionModel, DetailTransactionModel, ProductUnitDetailModel,
    PendingTransactionModel, TransactionTableItemModel, PurchasingHistoryTableItemModel,
    TransactionHistoryTableModel
)

from response.response_message import ResponseMessage
from generals.constants import (
    PERM_C_TRANSACTIONS, PERM_U_TRANSACTIONS, PERM_R_PENDING_TRANSACTIONS,
    PERM_C_PENDING_TRANSACTIONS, PERM_R_PENDING_TRANSACTIONS
)
from generals.messages import (
    ERR_PERM_C_TRANSACTIONS, ERR_PERM_U_TRANSACTIONS, ERR_PERM_R_PENDING_TRANSACTIONS,
    ERR_PERM_C_PENDING_TRANSACTIONS
)
from generals.permission_manager import PermissionManager


class TransactionRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()


    def submit_transaction(self, transaction: TransactionModel, detail_transactions: List[DetailTransactionModel]) -> ResponseMessage:
        if not self.permission_manager.has_permission(PERM_C_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_C_TRANSACTIONS)

        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get current timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert main transaction first
            sql = '''INSERT INTO transactions (transaction_id, customer_id, total_amount, payment_method, payment_rp, payment_change, 
                                                discount_amount, tax_pct, tax_amount, created_at, created_by, payment_remarks) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            
            transaction_id = transaction.transaction_id

            self.cursor.execute(sql, (transaction_id, transaction.customer_id, transaction.total_amount, transaction.payment_method, 
                                      transaction.payment_amount, transaction.payment_change, transaction.total_discount, 
                                      transaction.tax_pct, transaction.tax_amount, current_time, self.permission_manager.get_user_id(), transaction.payment_remarks))
            

            # Insert all detail transactions
            sql = '''INSERT INTO detail_transactions 
                    (transaction_id, sku, unit, unit_value, qty, price, discount_rp, discount_rp_per_item, discount_pct, sub_total) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
                

            for detail in detail_transactions:  
                sku = detail.sku
                qty = detail.qty
                unit_value = detail.unit_value
                unit = detail.unit
                stock_affected: int = int(qty) * int(unit_value)
                # Insert detail transaction
                self.cursor.execute(sql, (detail.transaction_id, sku, unit, unit_value, 
                                          qty, detail.price, detail.discount_rp, detail.discount_rp_per_item, 
                                          detail.discount_pct, detail.subtotal))
                
                # Update product stock
                update_sql = 'UPDATE products SET stock = stock - ? WHERE sku = ?'
                self.cursor.execute(update_sql, (stock_affected, sku))

                # Get updated stock value directly after update
                get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                self.cursor.execute(get_updated_stock_sql, (sku,))
                
                updated_stock = self.cursor.fetchone()[0]

                # Update Stock Card by Inserting Data to Stock Card Table
                stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''
                
                self.cursor.execute(stock_card_sql, (sku, transaction_id, None, stock_affected, updated_stock, ''))
                

            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(f"Transaction#{transaction_id} submitted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(f"Failed to submit transaction: {str(e)}")


    def update_transaction(self, transaction: TransactionModel, 
                            added_detail_transactions: List[DetailTransactionModel], 
                            updated_detail_transactions: List[DetailTransactionModel],
                            deleted_detail_transactions: List[DetailTransactionModel]) -> ResponseMessage:
        
        if not self.permission_manager.has_permission(PERM_U_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_U_TRANSACTIONS)

        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get current timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Update main transaction
            sql = '''UPDATE transactions 
                    SET customer_id = ?, total_amount = ?, payment_method = ?, payment_rp = ?, payment_change = ?, 
                        discount_amount = ?, tax_pct = ?, tax_amount = ?, payment_remarks = ?,
                        updated_at = ?, updated_by = ?
                    WHERE transaction_id = ?'''

            self.cursor.execute(sql, (transaction.customer_id, transaction.total_amount, transaction.payment_method, transaction.payment_amount, transaction.payment_change, 
                                      transaction.total_discount, transaction.tax_pct, transaction.tax_amount, transaction.payment_remarks, current_time, 
                                      self.permission_manager.get_user_id(), transaction.transaction_id))


            # Update updated detail transactions
            for updated_detail in updated_detail_transactions:
                # Get Old Stock
                get_old_stock_sql = 'SELECT qty FROM detail_transactions WHERE sku = ? and unit = ? and transaction_id = ?'
                self.cursor.execute(get_old_stock_sql, (updated_detail.sku, updated_detail.unit, updated_detail.transaction_id))

                old_stock = self.cursor.fetchone()[0]

                # If now stock is less than old stock, then update stock
                if int(updated_detail.qty) < int(old_stock):

                    # Add Stock if updated detail qty is less than old detail qty
                    stock_affected: int = int(old_stock) - int(updated_detail.qty)
                    update_sql = 'UPDATE products SET stock = stock + ? WHERE sku = ?'
                    self.cursor.execute(update_sql, (stock_affected, updated_detail.sku))

                    # Get updated stock value directly after update
                    get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                    self.cursor.execute(get_updated_stock_sql, (updated_detail.sku,))

                    updated_stock = self.cursor.fetchone()[0]


                    # Update Stock Card by Inserting Data to Stock Card Table
                    remarks = f'Correction Stock from Edit Transaction#{transaction.transaction_id} by {self.permission_manager.get_username()}'

                    stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''

                    self.cursor.execute(stock_card_sql, (updated_detail.sku, transaction.transaction_id, stock_affected, None, updated_stock, remarks))


                
                elif int(updated_detail.qty) > int(old_stock):
                    # Subtract Stock if updated detail qty is more than old detail qty
                    stock_affected: int = int(updated_detail.qty) - int(old_stock)

                    update_sql = 'UPDATE products SET stock = stock - ? WHERE sku = ?'
                    self.cursor.execute(update_sql, (stock_affected, updated_detail.sku))


                    # Get updated stock value directly after update
                    get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                    self.cursor.execute(get_updated_stock_sql, (updated_detail.sku,))

                    updated_stock = self.cursor.fetchone()[0]
                    
                    # Update Stock Card by Inserting Data to Stock Card Table
                    remarks = f'Correction Stock from Edit Transaction#{transaction.transaction_id} by {self.permission_manager.get_username()}'

                    stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''    
                    
                    self.cursor.execute(stock_card_sql, (updated_detail.sku, transaction.transaction_id, None, stock_affected, updated_stock, remarks)) 


                sql = '''UPDATE detail_transactions 
                        SET qty = ?, price = ?, discount_rp = ?, discount_rp_per_item = ?, discount_pct = ?, sub_total = ?
                         WHERE transaction_id = ? AND sku = ? AND unit = ?'''
                
                self.cursor.execute(sql, (updated_detail.qty, updated_detail.price, updated_detail.discount_rp, 
                                        updated_detail.discount_rp_per_item, updated_detail.discount_pct, updated_detail.subtotal, 
                                        updated_detail.transaction_id, updated_detail.sku, updated_detail.unit))


            # Delete detail transactions
            for deleted_detail in deleted_detail_transactions:
                sql = '''DELETE FROM detail_transactions WHERE transaction_id = ? AND sku = ? and unit = ?'''
                self.cursor.execute(sql, (transaction.transaction_id, deleted_detail.sku, deleted_detail.unit))


                # Update product stock
                stock_affected: int = int(deleted_detail.qty) * int(deleted_detail.unit_value)
                update_sql = 'UPDATE products SET stock = stock + ? WHERE sku = ?'
                self.cursor.execute(update_sql, (stock_affected, deleted_detail.sku))


                # Get updated stock value directly after update
                get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                self.cursor.execute(get_updated_stock_sql, (deleted_detail.sku,))

                updated_stock = self.cursor.fetchone()[0]


                # Update Stock Card by Inserting Data to Stock Card Table
                remarks = f'Correction Stock from Edit Transaction#{transaction.transaction_id} by {self.permission_manager.get_username()}'

                stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''

                self.cursor.execute(stock_card_sql, (deleted_detail.sku, transaction.transaction_id, stock_affected, None, updated_stock, remarks))


            # Insert added detail transactions
            for added_detail in added_detail_transactions:
                sql = '''INSERT INTO detail_transactions (transaction_id, sku, unit, unit_value, qty, 
                                                            price, discount_rp, discount_rp_per_item, 
                                                            discount_pct, sub_total) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''

                self.cursor.execute(sql, (added_detail.transaction_id, added_detail.sku, added_detail.unit, added_detail.unit_value, 
                                          added_detail.qty, added_detail.price, added_detail.discount_rp, added_detail.discount_rp_per_item, 
                                          added_detail.discount_pct, added_detail.subtotal))

                # Update product stock
                stock_affected: int = int(added_detail.qty) * int(added_detail.unit_value)
                update_sql = 'UPDATE products SET stock = stock - ? WHERE sku = ?'
                self.cursor.execute(update_sql, (stock_affected, added_detail.sku))

                # Get updated stock value directly after update
                get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                self.cursor.execute(get_updated_stock_sql, (added_detail.sku,))  


                updated_stock = self.cursor.fetchone()[0]

                # Update Stock Card by Inserting Data to Stock Card Table
                remarks = f'Correction Stock from Edit Transaction#{transaction.transaction_id} by {self.permission_manager.get_username()}'

                stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''

                self.cursor.execute(stock_card_sql, (added_detail.sku, transaction.transaction_id, None, stock_affected, updated_stock, remarks))


            self.db.commit()

            return ResponseMessage.ok(f"Transaction#{transaction.transaction_id} updated successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(f"Failed to update transaction: {str(e)}")


    def create_transaction_id(self, is_pending: bool = False) -> str:
        # Get Today's Date
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        # Get count of all transactions today   
        if is_pending:
            sql = '''SELECT COUNT(*) FROM pending_transactions WHERE created_at >= ? and created_at < ?'''
        else:
            sql = '''SELECT COUNT(*) FROM transactions WHERE created_at >= ? and created_at < ?'''

        self.cursor.execute(sql, (f'{today}', f'{tomorrow}'))

        transaction_count_today = self.cursor.fetchone()[0]
        transaction_count_today += 1

        transaction_id = f'A{datetime.now().strftime("%Y%m%d")}{transaction_count_today:04d}'
        if is_pending:
            transaction_id = f'P{datetime.now().strftime("%Y%m%d")}{transaction_count_today:04d}'

        while True:
            sql = '''SELECT COUNT(*) FROM transactions WHERE transaction_id = ?'''
            if is_pending:
                sql = '''SELECT COUNT(*) FROM pending_transactions WHERE transaction_id = ?'''

            self.cursor.execute(sql, (transaction_id,))
            count_id = self.cursor.fetchone()[0]

            if count_id == 0:
                break

            transaction_count_today += 1
            transaction_id = f'A{datetime.now().strftime("%Y%m%d")}{transaction_count_today:04d}'
            if is_pending:
                transaction_id = f'P{datetime.now().strftime("%Y%m%d")}{transaction_count_today:04d}'

        return transaction_id


    def create_pending_transaction(self, pending_transaction: PendingTransactionModel, detail_transactions: List[DetailTransactionModel]):
        if not self.permission_manager.has_permission(PERM_C_PENDING_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_C_PENDING_TRANSACTIONS)

        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get current timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert main transaction first
            sql = '''INSERT INTO pending_transactions (transaction_id, customer_id, total_amount, discount_transaction_id, discount_amount, created_at, payment_remarks) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            
            self.cursor.execute(sql, (pending_transaction.transaction_id, pending_transaction.customer_id, pending_transaction.total_amount, 
                                      pending_transaction.discount_transaction_id, pending_transaction.discount_amount, 
                                      current_time, pending_transaction.payment_remarks))
            
            # Insert all detail transactions
            sql = '''INSERT INTO pending_detail_transactions 

                    (transaction_id, sku, unit, unit_value, qty, price, discount_rp, discount_rp_per_item, discount_pct, sub_total) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
                

            for detail in detail_transactions:
                # Insert detail transaction
                self.cursor.execute(sql, (detail.transaction_id,  detail.sku, detail.unit, 
                                          detail.unit_value, detail.qty, detail.price, detail.discount_rp, 
                                          detail.discount_rp_per_item, detail.discount_pct, detail.subtotal))
                

            # If everything successful, commit the transaction
            self.db.commit()

            return ResponseMessage.ok("Transaction pending successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(f"Failed to create pending transaction: {str(e)}")


    def get_pending_transactions_by_id(self, transaction_id: str):
        if not self.permission_manager.has_permission(PERM_R_PENDING_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_R_PENDING_TRANSACTIONS)

        try:
            sql = '''SELECT pt.transaction_id, pt.customer_id, pt.total_amount, pt.discount_transaction_id, 
                            pt.discount_amount, pt.created_at, pt.payment_remarks
                    FROM pending_transactions pt
                    WHERE pt.transaction_id = ?
                    LIMIT 1'''
            
            self.cursor.execute(sql, (transaction_id,))
            
            result = self.cursor.fetchone()

            pending_transactions = PendingTransactionModel(
                transaction_id=result[0], customer_id=result[1], total_amount=result[2], discount_transaction_id=result[3],
                discount_amount=result[4], created_at=result[5], payment_remarks=result[6]
            )

            return ResponseMessage.ok(
                message="Transaction pending successfully!",
                data=pending_transactions
            )

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(f"Failed to add transaction: {str(e)}")


    def get_pending_transactions_details_by_id(self, transaction_id: str):
        if not self.permission_manager.has_permission(PERM_R_PENDING_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_R_PENDING_TRANSACTIONS)

        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            sql = '''SELECT p.sku, p.product_name, pdt.price, pdt.qty, pdt.unit, pdt.unit_value, pdt.discount_pct, 
                            pdt.discount_rp_per_item, pdt.discount_rp, pdt.sub_total
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
                        discount_pct=r[6], discount_rp_per_item=r[7],
                        discount_rp=r[8], subtotal=r[9]
                    )
                )

            return ResponseMessage.ok(
                message="Transaction pending successfully!",
                data=pending_detail_transactions
            )

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(f"Failed to add transaction: {str(e)}")


    def get_product_unit_details(self, sku: str) -> list[ProductUnitDetailModel]:
        try:
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
        
        except Exception as e:
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


    def get_customer_by_id(self, customer_id: str):
        try:
            sql = '''SELECT customer_name
                            FROM customers 
                     WHERE customer_id = ? 
                     LIMIT 1'''
            
            self.cursor.execute(sql, (customer_id,))
            result = self.cursor.fetchone()
            
            if result:
                return ResponseMessage.ok(
                    message="Customer fetched successfully!",
                    data=result[0]
                )
            
            return ResponseMessage.ok(
                message="Customer not found!",
                data=None
            )
            
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def get_purchasing_history_by_sku(self, sku: str):
        try:
            sql = '''SELECT ph.created_at, dph.qty, dph.unit
                    FROM detail_purchasing_history dph 
                    JOIN purchasing_history ph on ph.purchasing_id = dph.purchasing_id
                    WHERE dph.sku = ?
                    ORDER BY ph.created_at DESC'''
            
            self.cursor.execute(sql, (sku,))

            purchasing_history_results = self.cursor.fetchall()

            if purchasing_history_results:
                purchasing_history = [
                    PurchasingHistoryTableItemModel(created_at=ph[0], 
                                                    qty=ph[1], 
                                                    unit=ph[2]) 
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


    def get_transaction_history_by_sku(self, sku: str):
        try:
            sql = '''SELECT t.created_at, dt.qty, dt.unit
                        FROM detail_transactions dt
                        JOIN transactions t ON t.transaction_id = dt.transaction_id
                        WHERE dt.sku = ?
                        ORDER BY t.created_at DESC'''
            
            self.cursor.execute(sql, (sku,))

            transaction_history_results = self.cursor.fetchall()

            if transaction_history_results:
                transaction_history = [
                    TransactionHistoryTableModel(created_at=th[0], 
                                                    qty=th[1], 
                                                    unit=th[2]) 
                    for th in transaction_history_results
                ]

                return ResponseMessage.ok(
                    message="Transaction history fetched successfully!",
                    data=transaction_history
                )
            
            return ResponseMessage.ok(
                message="Transaction history not found!",
                data=None
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        

    def get_detail_transactions_by_id(self, transaction_id: str):
        try:
            sql = '''SELECT dt.sku, p.product_name, dt.price, dt.qty, dt.unit, dt.unit_value, dt.discount_pct ,
                            dt.discount_rp_per_item, dt.discount_rp, dt.sub_total
                    FROM detail_transactions dt
                    JOIN products p ON p.sku = dt.sku
                    WHERE dt.transaction_id = ?'''
            
            self.cursor.execute(sql, (transaction_id,))

            results = self.cursor.fetchall()
            
            if results:
                detail_transactions = [
                    TransactionTableItemModel(sku=r[0], product_name=r[1], price=r[2], qty=r[3], unit=r[4], unit_value=r[5],
                                           discount_pct=r[6], discount_rp_per_item=r[7], discount_rp=r[8], subtotal=r[9])
                    for r in results
                ]
                
                return ResponseMessage.ok(
                    message="Detail transactions fetched successfully!",
                    data=detail_transactions
                )
            
            return ResponseMessage.ok(message="Detail transactions not found!", data=None)


        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def get_transactions_by_id(self, transaction_id: str):
        try:
            sql = '''SELECT t.transaction_id, t.customer_id, t.total_amount, t.discount_amount, t.payment_method, t.payment_change, 
                            t.payment_remarks, t.tax_pct, t.tax_amount, t.created_at
                    FROM transactions t
                    WHERE t.transaction_id = ?
                    LIMIT 1'''
                    
            self.cursor.execute(sql, (transaction_id,))

            result = self.cursor.fetchone()
            transaction = TransactionModel(transaction_id=result[0], customer_id=result[1], total_amount=result[2], 
                                           total_discount=result[3], payment_method=result[4], payment_amount=result[2], 
                                           payment_change=result[5], payment_remarks=result[6], tax_pct=result[7], 
                                           tax_amount=result[8], created_at=result[9])
            return ResponseMessage.ok(
                message="Transaction fetched successfully!",    
                data=transaction
            )
            
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        
