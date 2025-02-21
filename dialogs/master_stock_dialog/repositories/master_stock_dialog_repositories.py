from connect_db import DatabaseConnection

from response.response_message import ResponseMessage
from dialogs.suppliers_dialog.models.suppliers_dialog_models import SupplierModel
from dialogs.master_stock_dialog.models.master_stock_dialog_models import PurchasingHistoryTableItemModel, MasterStockModel

class MasterStockDialogRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        
    
    def get_suppliers(self, search_text: str = ''):
        try:
            suppliers_result = []
            if search_text:
                sql = '''SELECT supplier_id, supplier_name, supplier_address, supplier_city, supplier_phone, supplier_remarks 
                            FROM suppliers
                            WHERE supplier_id LIKE ? OR supplier_name LIKE ? OR supplier_address LIKE ? OR supplier_city LIKE ? OR supplier_phone LIKE ? OR supplier_remarks LIKE ?'''
                
                search_text = f'%{search_text}%'
                suppliers_result = self.cursor.execute(sql, (search_text, search_text, search_text, search_text, search_text, search_text))
            else:
                sql = '''SELECT supplier_id, supplier_name, supplier_address, supplier_city, supplier_phone, supplier_remarks 
                            FROM suppliers'''

                suppliers_result = self.cursor.execute(sql)

            suppliers = [
                SupplierModel(supplier_id=r[0], supplier_name=r[1], supplier_address=r[2], supplier_city=r[3], supplier_phone=r[4], supplier_remarks=r[5]) 
                for r in suppliers_result
            ]

            return ResponseMessage.ok(
                message="Suppliers fetched successfully!",
                data=suppliers
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def get_purchasing_history_by_sku(self, sku: str):
        try:
            sql = '''SELECT ph.created_at, s.supplier_name, dph.qty, dph.unit, dph.price, 
                            dph.discount_rp, dph.discount_pct, dph.subtotal
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
                                                    discount_rp=ph[5], 
                                                    discount_pct=ph[6], 
                                                    subtotal=ph[7]) 
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
        

    def get_product_by_sku(self, sku: str):
        try:
            sql = '''SELECT p.product_name, p.barcode, p.category_id, p.supplier_id, p.unit, p.price, p.stock, p.remarks, 
                            c.category_name, s.supplier_name, p.last_price, p.average_price
                    FROM products p
                    LEFT JOIN categories c on c.category_id = p.category_id
                    LEFT JOIN suppliers s on s.supplier_id = p.supplier_id
                    WHERE p.sku = ?
                    LIMIT 1'''
            
            self.cursor.execute(sql, (sku,))

            result = self.cursor.fetchone()
            if result:
                return ResponseMessage.ok(
                    message="Success",
                    data=MasterStockModel(
                        sku=sku,
                        product_name=result[0],
                        barcode=result[1],
                        category_id=result[2],
                        supplier_id=result[3],
                        unit=result[4],
                        price=result[5],
                        stock=result[6],
                        remarks=result[7],
                        category_name=result[8],
                        supplier_name=result[9],
                        last_price=result[10],
                        average_price=result[11]
                    )
                )
            
            return ResponseMessage.ok(
                message="Success",
                data=None
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
