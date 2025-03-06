from connect_db import DatabaseConnection
from datetime import date
from response.response_message import ResponseMessage
from stock_card_list.models.stock_card_list_models import ProductStockCardListModel, StockCardListModel

class StockCardListRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        

    def get_products(self, search_text: str = None):
        try:
            products_result = []
            if search_text:
                sql = '''SELECT sku, product_name, stock, unit 
                            FROM products
                            WHERE sku LIKE ? OR product_name LIKE ? OR unit LIKE ?'''
                
                search_text = f'%{search_text}%'
                products_result = self.cursor.execute(sql, (search_text, search_text, search_text))
            else:
                sql = '''SELECT sku, product_name, stock, unit FROM products LIMIT 100'''
                products_result = self.cursor.execute(sql)

            product_list = [
                ProductStockCardListModel(sku=row[0], product_name=row[1], current_stock=row[2], unit=row[3])
                for row in products_result
            ]

            return ResponseMessage.ok(
                message="Products fetched successfully",
                data=product_list
            )

        except Exception as e:
            return ResponseMessage.fail(message=f"Error fetching products: {str(e)}")
        

    def get_stock_card(self, sku: str, start_date: date, end_date: date):
        try:
            stock_card_result = []
            sql = '''SELECT date, time, transaction_id, stock_in, stock_out, running_balance 
                        FROM stock_card 
                        WHERE sku = ? AND date BETWEEN ? AND ?'''
            
            stock_card_result = self.cursor.execute(sql, (sku, start_date, end_date))

            stock_card_list = [
                StockCardListModel(
                    date=row[0], time=row[1], transaction_id=row[2],
                    stock_in=row[3], stock_out=row[4], running_balance=row[5]
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
