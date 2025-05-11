from PyQt6 import QtWidgets, uic, QtCore
from datetime import datetime

from dialogs.suppliers_dialog.suppliers_dialog import SuppliersDialogWindow
from dialogs.master_stock_dialog.models.master_stock_dialog_models import MasterStockModel, PurchasingHistoryTableItemModel, CategoriesModel
from dialogs.master_stock_dialog.services.master_stock_dialog_services import MasterStockDialogService
from dialogs.suppliers_dialog.models.suppliers_dialog_models import SupplierModel
from dialogs.price_unit_dialog.price_unit_dialog import PriceUnitDialogWindow
from dialogs.products_dialog.products_dialog import ProductsDialogWindow
from dialogs.categories_dialog.categories_dialog import CategoriesDialogWindow

from helper import format_number, add_prefix, remove_non_digit
from generals.build import resource_path
from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import (
    RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS, 
    PERM_C_PRODUCTS, PERM_U_PRODUCTS, PERM_D_PRODUCTS,
)
from generals.messages import ( 
    ERR, OK, WARNING, CONFIRM, ERR_PERM_C_PRODUCTS, ERR_PERM_U_PRODUCTS, ERR_PERM_D_PRODUCTS,
    PERM_DENIED
)
from dialogs.master_stock_dialog.translations import MASTER_STOCK_DIALOG_TRANSLATIONS
from generals.permission_manager import PermissionManager
from generals.language_manager import LanguageManager


class MasterStockDialogWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.ui = uic.loadUi(resource_path('ui/master_stock.ui'), self)

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_C_PRODUCTS):
            return 

        # Init Dialog
        self.suppliers_dialog = SuppliersDialogWindow()
        self.price_unit_dialog = PriceUnitDialogWindow()
        self.products_dialog = ProductsDialogWindow()
        self.categories_dialog = CategoriesDialogWindow()

        # Init Services
        self.master_stock_dialog_service = MasterStockDialogService()

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(MASTER_STOCK_DIALOG_TRANSLATIONS)

        # Init Table
        self.purchasing_history_in_master_stock_table = self.ui.purchasing_history_in_master_stock_table

        # Connect the product_selected signal to handle_product_selected method
        self.products_dialog.product_selected.connect(self.handle_product_selected)
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

        # Event Filters
        self.ui.sku_master_stock_input.installEventFilter(self)
        self.ui.category_master_stock_input.installEventFilter(self)
        self.ui.supplier_master_stock_input.installEventFilter(self)
        self.ui.unit_master_stock_input.installEventFilter(self)
        self.ui.cost_price_master_stock_input.installEventFilter(self)
        self.ui.price_master_stock_input.installEventFilter(self)
        self.ui.stock_master_stock_input.installEventFilter(self)


        # Connect return pressed signal
        self.ui.sku_master_stock_input.returnPressed.connect(self.on_handle_sku_enter)
        self.ui.category_master_stock_input.returnPressed.connect(self.on_handle_category_enter)        
        self.ui.supplier_master_stock_input.returnPressed.connect(self.on_handle_supplier_enter)        

        self.ui.cost_price_master_stock_input.textChanged.connect(self.on_number_input_changed)
        self.ui.price_master_stock_input.textChanged.connect(self.on_number_input_changed)
        self.ui.stock_master_stock_input.textChanged.connect(self.on_number_input_changed)

        # Set selection behavior to select entire rows
        self.purchasing_history_in_master_stock_table.setSelectionBehavior(SELECT_ROWS)
        self.purchasing_history_in_master_stock_table.setSelectionMode(SINGLE_SELECTION)

        self.purchasing_history_in_master_stock_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties
        self.purchasing_history_in_master_stock_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.purchasing_history_in_master_stock_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)



    # Overrides
    # ===============
    def showEvent(self, event):
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_C_PRODUCTS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_C_PRODUCTS)
            self.close()
            return
        
        # Set window title
        if self.permission_manager.get_username().lower() not in self.windowTitle().lower():
            self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username())

        self.language_manager.translate_widget_text(self)   

        self.purchasing_history_headers = ['Date', 'Supplier Name', 'Qty', 'Unit', 'Price', 'Disc (%)', 'Disc (Rp)', 'Subtotal']
        if self.language_manager.get_current_language() == 'id':    
            self.purchasing_history_headers = ['Tanggal', 'Nama Supplier', 'Qty', 'Satuan', 'Harga', 'Diskon (%)', 'Diskon (Rp)', 'Subtotal']

        self.language_manager.translate_table_headers(self.ui.purchasing_history_in_master_stock_table, self.purchasing_history_headers)



    def handle_product_selected(self, product_data: dict):
        product_result = self.master_stock_dialog_service.get_product_by_sku(product_data['sku'])
        if product_result.success and product_result.data:
            self.set_master_stock_form_data(product_result.data)
            self.ui.category_master_stock_input.setFocus()


    def handle_supplier_selected(self, supplier_data: dict):
        supplier_result = self.master_stock_dialog_service.get_supplier_by_id(supplier_data['supplier_id'])
        if supplier_result.success and supplier_result.data:
            self.set_suppliers_form_data(supplier_result.data)
            self.ui.unit_master_stock_input.setFocus()



    def handle_category_selected(self, category_data: dict):
        category_result = self.master_stock_dialog_service.get_category_by_id(category_data['category_id'])
        if category_result.success and category_result.data:
            self.set_categories_form_data(category_result.data)
            self.ui.supplier_master_stock_input.setFocus()


    def create_new_master_stock(self):
        self.clear_master_stock_form()
        self.purchasing_history_in_master_stock_table.setRowCount(0)

    
    def submit_master_stock(self):
        if not self.permission_manager.has_permission(PERM_C_PRODUCTS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_C_PRODUCTS)
            return
        
        master_stock_form_data: MasterStockModel = self.get_master_stock_form_data()
        if not master_stock_form_data.sku or not master_stock_form_data.product_name \
            or not master_stock_form_data.unit or not master_stock_form_data.price \
            or not master_stock_form_data.stock:
            POSMessageBox.error(self, title=ERR, message="Please fill all required fields")
            return
        
        result = self.master_stock_dialog_service.submit_master_stock(master_stock_form_data)
        if result.success:
            POSMessageBox.info(self, title=OK, message=result.message)
            
            self.clear_master_stock_form()
            self.purchasing_history_in_master_stock_table.setRowCount(0)
            
        else:
            POSMessageBox.error(self, title=ERR, message=result.message)
    

    def update_master_stock(self):
        if not self.permission_manager.has_permission(PERM_U_PRODUCTS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_U_PRODUCTS)
            return
        
        master_stock_form_data: MasterStockModel = self.get_master_stock_form_data()
        sku = self.ui.sku_master_stock_input.text().strip()
        master_stock_form_data.sku = sku

        if not master_stock_form_data.sku:
            POSMessageBox.error(self, title=ERR, message="SKU is required")
            return
        
        result = self.master_stock_dialog_service.update_master_stock(master_stock_form_data)
        if result.success:
            POSMessageBox.info(self, title=OK, message=result.message)

            self.purchasing_history_in_master_stock_table.setRowCount(0)
            self.clear_master_stock_form()

        else:
            POSMessageBox.error(self, title=ERR, message=result.message)


    def delete_master_stock(self):
        if not self.permission_manager.has_permission(PERM_D_PRODUCTS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_D_PRODUCTS)
            return
        
        sku = self.ui.sku_master_stock_input.text().strip()

        if not sku:
            POSMessageBox.error(self, title=ERR, message="Please select a product to delete")
            return

        
        confirm = POSMessageBox.confirm(
                        self, title=CONFIRM, 
                        message=f'Are you sure you want to delete {sku} ?')

        if confirm:
            result = self.master_stock_dialog_service.delete_master_stock_by_sku(sku)
            if result.success:
                POSMessageBox.info(self, title=OK, message=result.message)

                self.purchasing_history_in_master_stock_table.setRowCount(0)
                self.clear_master_stock_form()

            else:
                POSMessageBox.error(self, title=ERR, message=result.message)

    # Shows
    # ===============
    def show_price_unit_dialog(self):
        sku = self.ui.sku_master_stock_input.text().strip()
        if not sku:
            POSMessageBox.error(self, title=ERR, message="Please select a product to set price unit")
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
        self.ui.category_master_stock_input.setText(str(data.category_id) if data.category_id else '')
        self.ui.category_name_master_stock_input.setText(data.category_name)
        self.ui.supplier_master_stock_input.setText(str(data.supplier_id) if data.supplier_id else '')
        self.ui.supplier_name_master_stock_input.setText(data.supplier_name)
        self.ui.unit_master_stock_input.setText(data.unit)
        self.ui.cost_price_master_stock_input.setText(add_prefix(format_number(str(data.cost_price))))
        self.ui.price_master_stock_input.setText(add_prefix(format_number(str(data.price))))
        self.ui.stock_master_stock_input.setText(format_number(str(data.stock)))
        self.ui.remarks_master_stock_input.setText(data.remarks)
        self.ui.last_price_master_stock_input.setText(add_prefix(format_number(str(int(data.last_price)))))
        self.ui.average_price_master_stock_input.setText(add_prefix(format_number(str(int(data.average_price)))))


    def set_master_stock_form_by_sku(self, sku: str):
        self.clear_master_stock_form()

        master_stock_result = self.master_stock_dialog_service.get_product_by_sku(sku)
        if master_stock_result.success and master_stock_result.data:
            self.purchasing_history_in_master_stock_table.setSortingEnabled(False)

            self.set_master_stock_form_data(master_stock_result.data)
            
            # Get Purchasing History
            purchasing_history_result = self.master_stock_dialog_service.get_purchasing_history_by_sku(sku)
            if purchasing_history_result.success and purchasing_history_result.data:
                self.set_purchasing_history_table_data(purchasing_history_result.data)
                
            self.ui.submit_master_stock_button.setText('Update')
            self.ui.submit_master_stock_button.clicked.disconnect()
            self.ui.submit_master_stock_button.clicked.connect(self.update_master_stock)
            self.ui.sku_master_stock_input.setFocus()


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

        self.purchasing_history_in_master_stock_table.setSortingEnabled(True)

    
    def set_categories_form_data(self, data: CategoriesModel):
        self.ui.category_master_stock_input.setText(str(data.category_id))
        self.ui.category_name_master_stock_input.setText(data.category_name)


    def set_suppliers_form_data(self, data: SupplierModel):
        self.ui.supplier_master_stock_input.setText(str(data.supplier_id))
        self.ui.supplier_name_master_stock_input.setText(data.supplier_name)


    # Getters
    # ===============
    def get_master_stock_form_data(self) -> MasterStockModel:
        sku = self.ui.sku_master_stock_input.text().strip().upper()
        product_name = self.ui.product_name_master_stock_input.text().strip().upper()
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

            # Focus to category input
            self.ui.category_master_stock_input.setFocus()

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

            # Focus to supplier input
            self.ui.supplier_master_stock_input.setFocus()

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

            # Focus to unit input
            self.ui.unit_master_stock_input.setFocus()

        else:
            # Supplier not found - show dialog with filter
            self.suppliers_dialog.set_filter(supplier_id)
            self.suppliers_dialog.show()


    def on_number_input_changed(self):
        self.ui.cost_price_master_stock_input.textChanged.disconnect()
        self.ui.price_master_stock_input.textChanged.disconnect()
        self.ui.stock_master_stock_input.textChanged.disconnect()

        cost_price = remove_non_digit(self.ui.cost_price_master_stock_input.text().strip()) if remove_non_digit(self.ui.cost_price_master_stock_input.text().strip()) != '' else '0'
        price = remove_non_digit(self.ui.price_master_stock_input.text().strip()) if remove_non_digit(self.ui.price_master_stock_input.text().strip()) != '' else '0'
        stock = remove_non_digit(self.ui.stock_master_stock_input.text().strip()) if remove_non_digit(self.ui.stock_master_stock_input.text().strip()) != '' else '0'

        self.ui.cost_price_master_stock_input.setText(add_prefix(format_number(str(int(cost_price)))))
        self.ui.price_master_stock_input.setText(add_prefix(format_number(str(int(price)))))
        self.ui.stock_master_stock_input.setText(format_number(str(int(stock))))

        self.ui.cost_price_master_stock_input.textChanged.connect(self.on_number_input_changed)
        self.ui.price_master_stock_input.textChanged.connect(self.on_number_input_changed)
        self.ui.stock_master_stock_input.textChanged.connect(self.on_number_input_changed)


    # Event Filters
    # ===============
    def eventFilter(self, obj, event):
        # If sku input is focused and key pressed is Enter it focus to category input
        if obj == self.ui.sku_master_stock_input and event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                self.on_handle_sku_enter()


        # If category input is focused and key pressed is Enter it focus to supplier input
        if obj == self.ui.category_master_stock_input and event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                self.on_handle_category_enter()


        # If supplier input is focused and key pressed is Enter it focus to unit input
        if obj == self.ui.supplier_master_stock_input and event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                self.on_handle_supplier_enter()


        # If unit input is focused and key pressed is Enter it focus to cost price input
        if obj == self.ui.unit_master_stock_input and event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                self.ui.cost_price_master_stock_input.setFocus()


        # If cost price input is focused and key pressed is Enter it focus to price input
        if obj == self.ui.cost_price_master_stock_input and event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                self.ui.price_master_stock_input.setFocus()


        # If price input is focused and key pressed is Enter it focus to stock input
        if obj == self.ui.price_master_stock_input and event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                self.ui.stock_master_stock_input.setFocus()


        return super().eventFilter(obj, event)
