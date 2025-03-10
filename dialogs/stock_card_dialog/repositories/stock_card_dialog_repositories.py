from connect_db import DatabaseConnection
from datetime import date

from dialogs.stock_card_dialog.models.stock_card_dialog_models import StockCardTableItemModel

from response.response_message import ResponseMessage

class StockCardDialogRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        

    def get_stock_card(self, sku: str, start_date: date, end_date: date):
        try:
            stock_card_result = []
            sql = '''SELECT date, time, transaction_id, stock_in, stock_out, running_balance, remarks 
                        FROM stock_card 
                        WHERE sku = ? AND date BETWEEN ? AND ?'''
            
            stock_card_result = self.cursor.execute(sql, (sku, start_date, end_date))

            stock_card_list = [
                StockCardTableItemModel(
                    date=row[0], time=row[1], transaction_id=row[2],
                    stock_in=row[3], stock_out=row[4], running_balance=row[5], 
                    remarks=row[6]
                )
                for row in stock_card_result
            ]

            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(
                message="Stock card fetched successfully!",
                data=stock_card_list
            )

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to fetch stock card {str(e)}")