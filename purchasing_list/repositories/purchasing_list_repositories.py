from datetime import datetime
from connect_db import DatabaseConnection

from response.response_message import ResponseMessage
from purchasing_list.models.purchasing_list_models import PurchasingListModel, DetailPurchasingModel

class PurchasingListRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        

    def get_purchasing_list(self, start_date: datetime, end_date: datetime, search_text: str = None):
        try:
            purchasing_result = []
            if search_text:
                sql = '''SELECT ph.created_at, ph.purchasing_id, s.supplier_name, ph.total_amount, ph.purchasing_remarks
                            FROM purchasing_history ph
                            LEFT JOIN suppliers s ON s.supplier_id = ph.supplier_id
                            WHERE ph.created_at BETWEEN ? AND ? 
                                AND (ph.purchasing_id LIKE ? OR ph.total_amount LIKE ? OR ph.purchasing_remarks LIKE ?)
                            ORDER BY ph.created_at DESC'''
                
                search_text = f'%{search_text}%'
                purchasing_result = self.cursor.execute(sql, (start_date, end_date, search_text, search_text, search_text, search_text))
            else:

                sql = '''SELECT ph.created_at, ph.purchasing_id, s.supplier_name, ph.total_amount, ph.purchasing_remarks 
                            FROM purchasing_history ph
                            LEFT JOIN suppliers s ON s.supplier_id = ph.supplier_id
                            WHERE ph.created_at BETWEEN ? AND ?
                            ORDER BY ph.created_at DESC'''
                purchasing_result = self.cursor.execute(sql, (start_date, end_date))
            
            purchasing_list = [
                PurchasingListModel(
                    created_at=row[0], purchasing_id=row[1],
                    supplier_name=row[2], total_amount=row[3], remarks=row[4]
                )
                for row in purchasing_result
            ]

            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(
                message="Purchasing list fetched successfully!",
                data=purchasing_list
            )

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to fetch purchasing list {str(e)}",
            )


    def get_detail_purchasing_by_id(self, purchasing_id: str):
        try:
            sql = '''SELECT dph.sku, p.product_name, dph.price, dph.qty, dph.unit, dph.discount_pct, dph.discount_rp, dph.subtotal
                    FROM detail_purchasing_history dph 
                    JOIN purchasing_history ph on ph.purchasing_id = dph.purchasing_id
                    JOIN products p ON p.sku = dph.sku
                    WHERE dph.purchasing_id = ?'''
            
            detail_purchasing_result = self.cursor.execute(sql, (purchasing_id,))
            
            # If everything successful, commit the transaction
            self.db.commit()

            detail_purchasing_list = [
                    DetailPurchasingModel(
                        sku=row[0], product_name=row[1], 
                    price=row[2], qty=row[3], unit=row[4], 
                    discount_rp=row[5], discount_pct=row[6], subtotal=row[7]
                )
                for row in detail_purchasing_result
            ]

            return ResponseMessage.ok(
                message="Purchasing detail fetched successfully!",
                data=detail_purchasing_list
            )
        
        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to fetch purchasing detail {str(e)}",
            )    