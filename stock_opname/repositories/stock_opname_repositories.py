from connect_db import DatabaseConnection
from typing import List
from stock_opname.models.stock_opname_models import StockOpnameModel

from response.response_message import ResponseMessage
from generals.constants import PERM_R_STOCK_OPNAME
from generals.messages import ERR_PERM_R_STOCK_OPNAME
from generals.permission_manager import PermissionManager


class StockOpnameRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()


    def get_stock_opname(self, search_text: str = None) -> List[StockOpnameModel]:
        if not self.permission_manager.has_permission(PERM_R_STOCK_OPNAME):
            return ResponseMessage.fail(message=ERR_PERM_R_STOCK_OPNAME)

        try:
            stock_opname_result = []
            if search_text:
                sql = '''SELECT sku, product_name, stock, unit
                            FROM products
                            WHERE sku LIKE ? OR product_name LIKE ? OR unit LIKE ?'''
                
                search_text = f'%{search_text}%'
                stock_opname_result = self.cursor.execute(sql, (search_text, search_text, search_text))
            else:

                sql = '''SELECT sku, product_name, stock, unit
                            FROM products'''
                stock_opname_result = self.cursor.execute(sql)
            
            stock_opname_list = [
                StockOpnameModel(
                    sku=row[0], product_name=row[1],
                    qty=row[2], unit=row[3]
                )
                for row in stock_opname_result
            ]

            # Commit Transaction
            self.db.commit()
            
            return ResponseMessage.ok(
                message="Stock Opname fetched successfully!",
                data=stock_opname_list
            )

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to fetch stock opname {str(e)}",
            )