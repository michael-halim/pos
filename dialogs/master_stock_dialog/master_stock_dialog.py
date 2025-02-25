from PyQt6 import QtWidgets, uic, QtGui, QtCore
from datetime import datetime
from helper import format_number, add_prefix, remove_non_digit

from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS

from dialogs.suppliers_dialog.suppliers_dialog import SuppliersDialogWindow
from dialogs.master_stock_dialog.models.master_stock_dialog_models import MasterStockModel, PurchasingHistoryTableItemModel, CategoriesModel
from dialogs.master_stock_dialog.services.master_stock_dialog_services import MasterStockDialogService
from dialogs.suppliers_dialog.models.suppliers_dialog_models import SupplierModel
from dialogs.price_unit_dialog.price_unit_dialog import PriceUnitDialogWindow
from dialogs.products_dialog.products_dialog import ProductsDialogWindow
from dialogs.categories_dialog.categories_dialog import CategoriesDialogWindow
from generals.build import resource_path

class MasterStockDialogWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.ui = uic.loadUi(resource_path('ui/master_stock.ui'), self)

        # Init Dialog
        self.suppliers_dialog = SuppliersDialogWindow()
        self.price_unit_dialog = PriceUnitDialogWindow()
        self.products_dialog = ProductsDialogWindow()
        self.categories_dialog = CategoriesDialogWindow()

        # Init Services
        self.master_stock_dialog_service = MasterStockDialogService()

        # Init Table
        self.purchasing_history_in_master_stock_table = self.ui.purchasing_history_in_master_stock_table
        self.purchasing_history_in_master_stock_table.setSortingEnabled(True)
        

        # Connect the product_selected signal to handle_product_selected method
        self.suppliers_dialog.supplier_selected.connect(self.handle_supplier_selected)
        self.categories_dialog.category_selected.connect(self.handle_category_selected)

        # Init Button
        self.ui.find_sku_master_stock_button.clicked.connect(lambda: self.products_dialog.show())
        self.ui.find_category_master_stock_button.clicked.connect(lambda: self.categories_dialog.show())
        self.ui.find_supplier_master_stock_button.clicked.connect(lambda: self.suppliers_dialog.show())

        
        self.ui.price_unit_master_stock_button.clicked.connect(self.show_price_unit_dialog)
        # self.ui.discount_master_stock_button.clicked.connect(self.discount_master_stock_button)
        self.ui.delete_master_stock_button.clicked.connect(self.delete_master_stock)
        self.ui.submit_master_stock_button.clicked.connect(self.submit_master_stock)
        self.ui.create_new_master_stock_button.clicked.connect(self.create_new_master_stock)
        
        self.ui.close_master_stock_button.clicked.connect(lambda: self.close())

        # Connect return pressed signal
        self.ui.sku_master_stock_input.returnPressed.connect(self.on_handle_sku_enter)
        self.ui.category_master_stock_input.returnPressed.connect(self.on_handle_category_enter)        
        self.ui.supplier_master_stock_input.returnPressed.connect(self.on_handle_supplier_enter)        

        # Set selection behavior to select entire rows
        self.purchasing_history_in_master_stock_table.setSelectionBehavior(SELECT_ROWS)
        self.purchasing_history_in_master_stock_table.setSelectionMode(SINGLE_SELECTION)

        self.purchasing_history_in_master_stock_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties
        self.purchasing_history_in_master_stock_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.purchasing_history_in_master_stock_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)


    def handle_supplier_selected(self, supplier_data: dict):
        supplier_result = self.master_stock_dialog_service.get_supplier_by_id(supplier_data['supplier_id'])
        if supplier_result.success and supplier_result.data:
            self.set_suppliers_form_data(supplier_result.data)


    def handle_category_selected(self, category_data: dict):
        category_result = self.master_stock_dialog_service.get_category_by_id(category_data['category_id'])
        if category_result.success and category_result.data:
            self.set_categories_form_data(category_result.data)


    def create_new_master_stock(self):
        self.clear_master_stock_form()
        self.purchasing_history_in_master_stock_table.setRowCount(0)

    
    def submit_master_stock(self):
        master_stock_form_data: MasterStockModel = self.get_master_stock_form_data()
        if not master_stock_form_data.sku or not master_stock_form_data.product_name \
            or not master_stock_form_data.unit or not master_stock_form_data.price \
            or not master_stock_form_data.stock:
            POSMessageBox.error(self, title='Error', message="Please fill all required fields")
            return
        
        result = self.master_stock_dialog_service.submit_master_stock(master_stock_form_data)
        if result.success:
            POSMessageBox.info(self, title='Success', message=result.message)
            
            self.clear_master_stock_form()
            self.purchasing_history_in_master_stock_table.setRowCount(0)
            
        else:
            POSMessageBox.error(self, title='Error', message=result.message)
    

    def update_master_stock(self):
        master_stock_form_data: MasterStockModel = self.get_master_stock_form_data()
        sku = self.ui.sku_master_stock_input.text().strip()
        master_stock_form_data.sku = sku

        if not master_stock_form_data.sku:
            POSMessageBox.error(self, title='Error', message="SKU is required")
            return
        
        result = self.master_stock_dialog_service.update_master_stock(master_stock_form_data)
        if result.success:
            POSMessageBox.info(self, title='Success', message=result.message)

            self.purchasing_history_in_master_stock_table.setRowCount(0)
            self.clear_master_stock_form()

        else:
            POSMessageBox.error(self, title='Error', message=result.message)


    def delete_master_stock(self):
        sku = self.ui.sku_master_stock_input.text().strip()

        if not sku:
            POSMessageBox.error(self, title='Error', message="Please select a product to delete")
            return

        
        confirm = POSMessageBox.confirm(
                        self, title='Confirm Deletion', 
                        message=f'Are you sure you want to delete {sku} ?')

        if confirm:
            result = self.master_stock_dialog_service.delete_master_stock_by_sku(sku)
            if result.success:
                POSMessageBox.info(self, title='Success', message=result.message)

                self.purchasing_history_in_master_stock_table.setRowCount(0)
                self.clear_master_stock_form()

            else:
                POSMessageBox.error(self, title='Error', message=result.message)

    # Shows
    # ===============
    def show_price_unit_dialog(self):
        sku = self.ui.sku_master_stock_input.text().strip()
        if not sku:
            POSMessageBox.error(self, title='Error', message="Please select a product to set price unit")
            return
        
        self.price_unit_dialog.set_price_unit_form_by_sku(sku)
        self.price_unit_dialog.show()


    # Clears
    # ===============
    def clear_master_stock_form(self):
        self.ui.submit_master_stock_button.setText('Submit')
        self.ui.submit_master_stock_button.clicked.disconnect()
        self.ui.submit_master_stock_button.clicked.connect(self.submit_master_stock)

        self.ui.sku_master_stock_input.clear()
        self.ui.product_name_master_stock_input.clear()
        self.ui.unit_master_stock_input.clear()
        self.ui.barcode_master_stock_input.clear()
        self.ui.cost_price_master_stock_input.clear()
        self.ui.price_master_stock_input.clear()
        self.ui.stock_master_stock_input.clear()
        self.ui.remarks_master_stock_input.clear()
        self.ui.category_master_stock_input.clear()
        self.ui.category_name_master_stock_input.clear()
        self.ui.supplier_master_stock_input.clear()
        self.ui.supplier_name_master_stock_input.clear()
        self.ui.last_price_master_stock_input.clear()
        self.ui.average_price_master_stock_input.clear()


    # Setters
    # ===============
    def set_master_stock_form_data(self, data: MasterStockModel):
        # Check if price, stock, and cost_price is not None and not empty
        data.cost_price = int(data.cost_price) if data.cost_price is not None and data.cost_price != '' else 0
        data.price = int(data.price) if data.price is not None and data.price != '' else 0
        data.stock = int(data.stock) if data.stock is not None and data.stock != '' else 0
        
        self.ui.sku_master_stock_input.setText(data.sku)
        self.ui.product_name_master_stock_input.setText(data.product_name)
        self.ui.barcode_master_stock_input.setText(data.barcode)
        self.ui.category_master_stock_input.setText(str(data.category_id))
        self.ui.category_name_master_stock_input.setText(data.category_name)
        self.ui.supplier_master_stock_input.setText(str(data.supplier_id))
        self.ui.supplier_name_master_stock_input.setText(data.supplier_name)
        self.ui.unit_master_stock_input.setText(data.unit)
        self.ui.cost_price_master_stock_input.setValue(int(data.cost_price))
        self.ui.price_master_stock_input.setValue(int(data.price))
        self.ui.stock_master_stock_input.setValue(int(data.stock))
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
                self.ui.submit_master_stock_button.setText('Update')
                self.ui.submit_master_stock_button.clicked.disconnect()
                self.ui.submit_master_stock_button.clicked.connect(self.update_master_stock)


    def set_purchasing_history_table_data(self, data: list[PurchasingHistoryTableItemModel]):
        # Clear Purchasing History Table
        self.purchasing_history_in_master_stock_table.setRowCount(0)

        for purchasing_history in data:
            current_row = self.purchasing_history_in_master_stock_table.rowCount()
            self.purchasing_history_in_master_stock_table.insertRow(current_row)

            # Convert created_at string to datetime and format
            created_at_dt = datetime.strptime(purchasing_history.created_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = created_at_dt.strftime('%d %b %y %H:%M')

            table_items =  [ 
                QtWidgets.QTableWidgetItem(formatted_date),
                QtWidgets.QTableWidgetItem(purchasing_history.supplier_name),
                QtWidgets.QTableWidgetItem(format_number(purchasing_history.qty)),
                QtWidgets.QTableWidgetItem(purchasing_history.unit),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(purchasing_history.price))),
                QtWidgets.QTableWidgetItem(format_number(purchasing_history.discount_pct)),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(purchasing_history.discount_rp))),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(purchasing_history.subtotal)))
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.purchasing_history_in_master_stock_table.setItem(current_row, col, item)

    
    def set_categories_form_data(self, data: CategoriesModel):
        self.ui.category_master_stock_input.setText(str(data.category_id))
        self.ui.category_name_master_stock_input.setText(data.category_name)


    def set_suppliers_form_data(self, data: SupplierModel):
        self.ui.supplier_master_stock_input.setText(str(data.supplier_id))
        self.ui.supplier_name_master_stock_input.setText(data.supplier_name)

    # Getters
    # ===============
    def get_master_stock_form_data(self) -> MasterStockModel:
        sku = self.ui.sku_master_stock_input.text().strip()
        product_name = self.ui.product_name_master_stock_input.text().strip()
        barcode = self.ui.barcode_master_stock_input.text().strip()
        category_id = self.ui.category_master_stock_input.text().strip()
        category_name = self.ui.category_name_master_stock_input.text().strip()
        supplier_id = self.ui.supplier_master_stock_input.text().strip()
        supplier_name = self.ui.supplier_name_master_stock_input.text().strip()
        unit = self.ui.unit_master_stock_input.text().strip()
        cost_price = remove_non_digit(self.ui.cost_price_master_stock_input.text().strip()) if self.ui.cost_price_master_stock_input.text().strip() else 0
        price = remove_non_digit(self.ui.price_master_stock_input.text().strip())
        stock = remove_non_digit(self.ui.stock_master_stock_input.text().strip())
        remarks = self.ui.remarks_master_stock_input.toPlainText().strip()
        last_price = remove_non_digit(self.ui.last_price_master_stock_input.text().strip())
        average_price = remove_non_digit(self.ui.average_price_master_stock_input.text().strip())
        
        return MasterStockModel(
            sku=sku,
            product_name=product_name,
            barcode=barcode,
            category_id=category_id,
            category_name=category_name,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            unit=unit,
            cost_price=cost_price,
            price=price,
            stock=stock,
            remarks=remarks,
            last_price=last_price,
            average_price=average_price
        )
    

    # Event Listeners
    # ===============
    def on_handle_sku_enter(self):
        sku = self.ui.sku_master_stock_input.text().strip().upper()
        if not sku:
            self.clear_master_stock_form()
            return

        # Try to find exact SKU match
        result = self.master_stock_dialog_service.get_product_by_sku(sku)
        if result.success and result.data:
            # Product found - fill the form
            self.set_master_stock_form_by_sku(sku)
            
        else:
            # Product not found - show dialog with filter
            self.products_dialog.set_filter(sku)
            self.products_dialog.show()


    def on_handle_category_enter(self):
        category_id = self.ui.category_master_stock_input.text().strip()
        if not category_id:
            return

        # Try to find exact Category Id match
        result = self.master_stock_dialog_service.get_category_by_id(category_id)
        if result.success and result.data:
            # Category found - fill the form
            self.handle_category_selected({'category_id': result.data.category_id})

        else:
            # Category not found - show dialog with filter
            self.categories_dialog.set_filter(category_id)
            self.categories_dialog.show()


    def on_handle_supplier_enter(self):
        supplier_id = self.ui.supplier_master_stock_input.text().strip()
        if not supplier_id:
            return

        # Try to find exact Supplier Id match
        result = self.master_stock_dialog_service.get_supplier_by_id(supplier_id)
        if result.success and result.data:
            # Supplier found - fill the form
            self.handle_supplier_selected({'supplier_id': result.data.supplier_id})

        else:
            # Supplier not found - show dialog with filter
            self.suppliers_dialog.set_filter(supplier_id)
            self.suppliers_dialog.show()