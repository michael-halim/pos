from connect_db import DatabaseConnection

from dialogs.pending_transactions_dialog.models.pending_transactions_dialog_models import PendingTransactionModel, PendingDetailTransactionModel

from response.response_message import ResponseMessage

class PendingTransactionsDialogRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        

    def get_pending_transactions(self, search_text: str = None):
        try:
            pending_transactions_result = []
            if search_text:
                sql = '''SELECT transaction_id, customer_id, total_amount, created_at, payment_remarks, discount_amount, discount_transaction_id
                            FROM pending_transactions
                            WHERE transaction_id LIKE ? OR customer_id LIKE ? OR total_amount LIKE ? OR created_at LIKE ? OR payment_remarks LIKE ? OR discount_amount LIKE ?'''
                
                search_text = f'%{search_text}%'
                pending_transactions_result = self.cursor.execute(sql, (search_text, search_text, search_text, search_text, search_text, search_text))
            else:
                sql = '''SELECT transaction_id, customer_id, total_amount, created_at, payment_remarks, discount_amount, discount_transaction_id
                            FROM pending_transactions'''
                pending_transactions_result = self.cursor.execute(sql)

            pending_transactions = [
                PendingTransactionModel(transaction_id=r[0], customer_id=r[1], total_amount=r[2], created_at=r[3], 
                                        payment_remarks=r[4], discount_amount=r[5], discount_transaction_id=r[6]) 
                for r in pending_transactions_result
            ]

            return ResponseMessage.ok(
                message="Pending transactions fetched successfully!",
                data=pending_transactions
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        

    def get_pending_detail_transactions(self, transaction_id: str):
        try:
            sql = '''SELECT p.sku, p.product_name, pdt.price, pdt.qty, pdt.unit, pdt.discount_pct, 
                            pdt.discount_rp_per_item, pdt.discount_rp, pdt.sub_total
                    FROM pending_detail_transactions pdt
                    JOIN products p ON p.sku = pdt.sku and p.unit = pdt.unit
                    WHERE pdt.transaction_id = ?'''
                    
            pending_detail_transactions_result = self.cursor.execute(sql, (transaction_id,))    

            pending_detail_transactions = [
                PendingDetailTransactionModel(sku=r[0], product_name=r[1], price=r[2], 
                                              qty=r[3], unit=r[4], discount_pct=r[5], discount_rp_per_item=r[6], 
                                              discount_rp=r[7], subtotal=r[8]) 
                for r in pending_detail_transactions_result
            ]

            return ResponseMessage.ok(
                message="Pending detail transactions fetched successfully!",
                data=pending_detail_transactions
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")

