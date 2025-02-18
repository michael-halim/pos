from PyQt6 import QtWidgets, uic, QtGui, QtCore

from helper import format_number, add_prefix, remove_non_digit

from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS

from dialogs.suppliers_dialog.suppliers_dialog import SuppliersDialogWindow
from dialogs.master_stock_dialog.models.master_stock_dialog_models import MasterStockModel, PurchasingHistoryTableItemModel

from dialogs.master_stock_dialog.services.master_stock_dialog_services import MasterStockDialogService
from dialogs.price_unit_dialog.price_unit_dialog import PriceUnitDialogWindow

class MasterStockDialogWindow(QtWidgets.QWidget):
    
    def __init__(self):
        super().__init__()

        self.ui = uic.loadUi('./ui/master_stock.ui', self)

        # Init Dialog
        self.suppliers_dialog = SuppliersDialogWindow()
        self.price_unit_dialog = PriceUnitDialogWindow()

        # Init Services
        self.master_stock_dialog_service = MasterStockDialogService()

        # Init Table
        self.purchasing_history_in_master_stock_table = self.ui.purchasing_history_in_master_stock_table
        self.purchasing_history_in_master_stock_table.setSortingEnabled(True)
        
        # Init Button
        self.ui.find_sku_master_stock_button.clicked.connect(self.find_sku)
        self.ui.find_category_master_stock_button.clicked.connect(self.find_category)
        self.ui.find_supplier_master_stock_button.clicked.connect(lambda: self.suppliers_dialog.show())

        
        self.ui.price_unit_master_stock_button.clicked.connect(lambda: self.price_unit_dialog.show())
        # self.ui.discount_master_stock_button.clicked.connect(self.discount_master_stock_button)
        # self.ui.delete_master_stock_button.clicked.connect(self.delete_master_stock_button)
        # self.ui.submit_master_stock_button.clicked.connect(self.submit_master_stock_button)
        self.ui.create_new_master_stock_button.clicked.connect(self.create_new_master_stock)
        
        self.ui.close_master_stock_button.clicked.connect(lambda: self.close())


        # Set selection behavior to select entire rows
        self.purchasing_history_in_master_stock_table.setSelectionBehavior(SELECT_ROWS)
        self.purchasing_history_in_master_stock_table.setSelectionMode(SINGLE_SELECTION)

        self.purchasing_history_in_master_stock_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties
        self.purchasing_history_in_master_stock_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.purchasing_history_in_master_stock_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

       
    def find_sku(self):
        pass
    
    def find_category(self):
        pass
    

    def show_purchasing_history(self):
        sku = self.ui.sku_purchasing_input.text().strip()
        if not sku:
            return
        
        purchasing_history_result = self.master_stock_dialog_service.get_purchasing_history_by_sku(sku)
        if purchasing_history_result.success and purchasing_history_result.data:
            self.set_purchasing_history_table_data(purchasing_history_result.data)


    def set_purchasing_history_table_data(self, data: list[PurchasingHistoryTableItemModel]):
        # Clear Purchasing History Table
        self.purchasing_history_in_master_stock_table.setRowCount(0)

        for purchasing_history in data:
            current_row = self.purchasing_history_in_master_stock_table.rowCount()
            self.purchasing_history_in_master_stock_table.insertRow(current_row)

            table_items =  [ 
                QtWidgets.QTableWidgetItem(purchasing_history.created_at),
                QtWidgets.QTableWidgetItem(purchasing_history.supplier_name),
                QtWidgets.QTableWidgetItem(format_number(purchasing_history.qty)),
                QtWidgets.QTableWidgetItem(purchasing_history.unit),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(purchasing_history.price))),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(purchasing_history.subtotal)))
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=14))
                self.purchasing_history_in_master_stock_table.setItem(current_row, col, item)


    def clear_master_stock_form(self):
        self.ui.sku_master_stock_input.clear()
        self.ui.product_name_master_stock_input.clear()
        self.ui.unit_master_stock_input.clear()
        self.ui.barcode_master_stock_input.clear()
        self.ui.price_master_stock_input.clear()
        self.ui.stock_master_stock_input.clear()
        self.ui.remarks_master_stock_input.clear()
        self.ui.category_master_stock_input.clear()
        self.ui.category_name_master_stock_input.clear()
        self.ui.supplier_master_stock_input.clear()
        self.ui.supplier_name_master_stock_input.clear()
        self.ui.last_price_master_stock_input.clear()
        self.ui.average_price_master_stock_input.clear()


    def create_new_master_stock(self):
        self.clear_master_stock_form()
        self.purchasing_history_in_master_stock_table.setRowCount(0)


    
    def get_master_stock_form_data(self) -> MasterStockModel | None:
        sku = self.ui.sku_master_stock_input.text().strip()
        product_name = self.ui.product_name_master_stock_input.text().strip()
        barcode = self.ui.barcode_master_stock_input.text().strip()
        category_id = self.ui.category_master_stock_input.text().strip()
        category_name = self.ui.category_name_master_stock_input.text().strip()
        supplier_id = self.ui.supplier_master_stock_input.text().strip()
        supplier_name = self.ui.supplier_name_master_stock_input.text().strip()
        unit = self.ui.unit_master_stock_input.text().strip()
        price = remove_non_digit(self.ui.price_master_stock_input.text().strip())
        stock = remove_non_digit(self.ui.stock_master_stock_input.text().strip())
        remarks = self.ui.remarks_master_stock_input.text().strip()
        last_price = remove_non_digit(self.ui.last_price_master_stock_input.text().strip())
        average_price = remove_non_digit(self.ui.average_price_master_stock_input.text().strip())
        
        # TODO: Check if the data is valid
        if sku == '' or product_name == '' or unit == '' or barcode == '' or price == '' or stock == '':
            return None
        
        return MasterStockModel(
            sku=sku,
            product_name=product_name,
            barcode=barcode,
            category_id=category_id,
            category_name=category_name,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            unit=unit,
            price=price,
            stock=stock,
            remarks=remarks,
            last_price=last_price,
            average_price=average_price
        )
       

    def set_master_stock_form_data(self, data: MasterStockModel):
        self.ui.sku_master_stock_input.setText(data.sku)
        self.ui.product_name_master_stock_input.setText(data.product_name)
        self.ui.barcode_master_stock_input.setText(data.barcode)
        self.ui.category_master_stock_input.setText(str(data.category_id))
        self.ui.category_name_master_stock_input.setText(data.category_name)
        self.ui.supplier_master_stock_input.setText(str(data.supplier_id))
        self.ui.supplier_name_master_stock_input.setText(data.supplier_name)
        self.ui.unit_master_stock_input.setText(data.unit)
        self.ui.price_master_stock_input.setValue(data.price)
        self.ui.stock_master_stock_input.setValue(data.stock)
        self.ui.remarks_master_stock_input.setText(data.remarks)
        self.ui.last_price_master_stock_input.setText(add_prefix(format_number(data.last_price)))
        self.ui.average_price_master_stock_input.setText(add_prefix(format_number(data.average_price)))


    def set_master_stock_form_by_sku(self, sku: str):
        self.clear_master_stock_form()

        master_stock_result = self.master_stock_dialog_service.get_product_by_sku(sku)
        if master_stock_result.success and master_stock_result.data:
            self.set_master_stock_form_data(master_stock_result.data)
            
            # Get Purchasing History
            purchasing_history_result = self.master_stock_dialog_service.get_purchasing_history_by_sku(sku)
            if purchasing_history_result.success and purchasing_history_result.data:
                self.set_purchasing_history_table_data(purchasing_history_result.data)
