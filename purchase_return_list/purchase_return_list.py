from PyQt6 import QtWidgets, uic

from purchase_return_list.services.purchase_return_list_services import PurchaseReturnListService
from purchase_return_list.models.purchase_return_list_models import PurchaseReturnListModel

from helper import format_number, add_prefix, remove_non_digit
from generals.message_box import POSMessageBox
from generals.build import resource_path
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    PERM_R_PURCHASE_RETURN, PERM_C_PURCHASE_RETURN, 
    PERM_U_PURCHASE_RETURN, PERM_D_PURCHASE_RETURN, DATE_FORMAT_DDMMYYYY
) 
from generals.messages import (
    ERR, OK, ERR_PERM_R_PURCHASE_RETURN, ERR_PERM_C_PURCHASE_RETURN, 
    ERR_PERM_U_PURCHASE_RETURN, ERR_PERM_D_PURCHASE_RETURN,
    PERM_DENIED
)
from purchase_return_list.translations import PURCHASE_RETURN_LIST_TRANSLATIONS
from generals.permission_manager import PermissionManager
from generals.language_manager import LanguageManager
from purchase_return.purchase_return import PurchaseReturnWindow
from datetime import datetime
from purchase_return.models.purchase_return_models import DetailPurchaseReturnModel
from generals.fonts import POSFonts


class PurchaseReturnListWindow(QtWidgets.QWidget):
    def __init__(self, home_window: None):
        super().__init__()

        self.home_window = home_window

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_PURCHASE_RETURN):   
            return


        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/purchase_return_list.ui'), self)

        # Init Services
        self.purchase_return_list_service = PurchaseReturnListService()
        
        # Init Windows
        self.purchase_return_window = PurchaseReturnWindow()

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(PURCHASE_RETURN_LIST_TRANSLATIONS)
        
        # Connect Filter Purchase Return
        self.ui.filter_purchase_return_list_input.textChanged.connect(self.show_purchase_return_data)
        self.ui.filter_detail_purchase_return_list_input.textChanged.connect(self.filter_detail_purchase_return)

        # Connect Buttons
        self.ui.find_purchase_return_list_button.clicked.connect(self.show_purchase_return_data)
        self.ui.edit_purchase_return_button.clicked.connect(self.edit_purchase_return)
        self.ui.delete_purchase_return_button.clicked.connect(self.delete_purchase_return)
        self.ui.create_purchase_return_button.clicked.connect(self.create_purchase_return)
        self.ui.close_purchase_return_list_button.clicked.connect(lambda: self.close())

        # Init Tables
        self.purchase_return_table = self.ui.purchase_return_table
        self.detail_purchase_return_table = self.ui.detail_purchase_return_table

        # Connect table selection
        self.purchase_return_table.itemSelectionChanged.connect(self.on_purchase_return_selected)
        
        # Set date input
        self.ui.start_date_purchase_return_list_input.setDate(datetime.now())
        self.ui.end_date_purchase_return_list_input.setDate(datetime.now())

        self.ui.start_date_purchase_return_list_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)
        self.ui.end_date_purchase_return_list_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)

        # Add selected tracking
        self.current_selected_sku = None
     
        # Set selection behavior to select entire rows
        self.purchase_return_table.setSelectionBehavior(SELECT_ROWS)
        self.purchase_return_table.setSelectionMode(SINGLE_SELECTION)
        self.detail_purchase_return_table.setSelectionBehavior(SELECT_ROWS)
        self.detail_purchase_return_table.setSelectionMode(SINGLE_SELECTION)

        # Set wholesale purchase return table to be read only
        self.purchase_return_table.setEditTriggers(NO_EDIT_TRIGGERS)
        self.detail_purchase_return_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.purchase_return_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.purchase_return_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.detail_purchase_return_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.detail_purchase_return_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        # Show data for both tables
        self.show_purchase_return_data()


    # Overrides
    # ===============
    def showEvent(self, event):
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_R_PURCHASE_RETURN):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_R_PURCHASE_RETURN)
            return

        # Set window title
        if self.permission_manager.get_username().lower() not in self.windowTitle().lower():
            self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username())

        # Translate Widget Text
        self.language_manager.translate_widget_text(self)

        self.purchase_return_table_headers = ['Date', 'Purchase Return #', 'Supplier Name', 'Total', 'Remarks']
        self.detail_purchase_return_table_headers = ['SKU', 'Product Name', 'Price', 'Qty', 'Unit', 'Subtotal']

        if self.language_manager.get_current_language() == 'id':    
            self.purchase_return_table_headers = ['Tanggal', 'ID Return Pembelian', 'Nama Supplier', 'Total', 'Keterangan']
            self.detail_purchase_return_table_headers = ['Kode Barang', 'Nama Produk', 'Harga', 'Qty', 'Satuan', 'Subtotal']

        self.language_manager.translate_table_headers(self.ui.purchase_return_table, self.purchase_return_table_headers)
        self.language_manager.translate_table_headers(self.ui.detail_purchase_return_table, self.detail_purchase_return_table_headers)


        # Refresh the data
        self.show_purchase_return_data()


    def show(self):
        super().show()
        if not self.permission_manager.has_permission(PERM_R_PURCHASE_RETURN):
            self.close()
            return

        # Refresh the data
        self.show_purchase_return_data() 


    def showMaximized(self):
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_R_PURCHASE_RETURN):
            self.close()
            return

        # Refresh the data
        self.show_purchase_return_data()


    def create_purchase_return(self):
        if not self.permission_manager.has_permission(PERM_C_PURCHASE_RETURN):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_C_PURCHASE_RETURN)
            return

        self.purchase_return_window.showMaximized()


    def edit_purchase_return(self):
        if not self.permission_manager.has_permission(PERM_U_PURCHASE_RETURN):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_U_PURCHASE_RETURN)
            return

        selected_rows = self.purchase_return_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title=ERR, message="Please select a purchase return to edit")
            return
        
        row = selected_rows[0].row()
        purchase_return_id = self.purchase_return_table.item(row, 1).text()

        self.purchase_return_window.set_purchase_return_by_id(purchase_return_id)
        self.purchase_return_window.showMaximized()


    def delete_purchase_return(self):
        if not self.permission_manager.has_permission(PERM_D_PURCHASE_RETURN):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_D_PURCHASE_RETURN)
            return

        selected_rows = self.purchase_return_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title=ERR, message="Please select a purchase return to delete")
            return
        
        row = selected_rows[0].row()
        purchase_return_id = self.purchase_return_table.item(row, 1).text()

        confirm = POSMessageBox.confirm(
                    self, title='Confirm Deletion', 
                    message=f'Are you sure you want to delete {purchase_return_id} ?')

        if confirm:
            result = self.purchase_return_list_service.delete_purchase_return_by_id(purchase_return_id)
            if result.success:
                POSMessageBox.info(self, title=OK, message=result.message)

                # Just refresh the data directly
                self.show_purchase_return_data()

            else:
                POSMessageBox.error(self, title=ERR, message=result.message)


    # Setters
    # ===============
    def set_purchase_return_table_data(self, data: list[PurchaseReturnListModel]):
        # Clear the table
        self.purchase_return_table.setRowCount(0)
        total_purchase_return = 0
        for purchase_return in data:
            current_row = self.purchase_return_table.rowCount()
            self.purchase_return_table.insertRow(current_row)

            # Convert created_at string to datetime and format
            created_at_dt = datetime.strptime(purchase_return.created_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = created_at_dt.strftime('%d %b %y %H:%M')

            table_items =  [ 
                QtWidgets.QTableWidgetItem(formatted_date),
                QtWidgets.QTableWidgetItem(purchase_return.purchase_return_id),
                QtWidgets.QTableWidgetItem(purchase_return.supplier_name),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(purchase_return.total_amount))),
                QtWidgets.QTableWidgetItem(purchase_return.remarks),
            ]

            total_purchase_return += purchase_return.total_amount

            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.purchase_return_table.setItem(current_row, col, item)

        self.ui.total_purchase_return_input.setText(add_prefix(format_number(total_purchase_return)))

        self.purchase_return_table.setSortingEnabled(True)


    def set_detail_purchase_return_table_data(self, data: list[DetailPurchaseReturnModel]):
        # Clear the table
        self.detail_purchase_return_table.setRowCount(0)

        for detail_purchase_return in data:
            current_row = self.detail_purchase_return_table.rowCount()
            self.detail_purchase_return_table.insertRow(current_row)


            table_items =  [ 
                QtWidgets.QTableWidgetItem(detail_purchase_return.sku),
                QtWidgets.QTableWidgetItem(detail_purchase_return.product_name),
                QtWidgets.QTableWidgetItem(format_number(detail_purchase_return.price)),
                QtWidgets.QTableWidgetItem(format_number(detail_purchase_return.qty)),
                QtWidgets.QTableWidgetItem(detail_purchase_return.unit),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(detail_purchase_return.subtotal)))
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.detail_purchase_return_table.setItem(current_row, col, item)
        
        self.detail_purchase_return_table.setSortingEnabled(True)
 

    # Shows
    # ===============
    def show_purchase_return_data(self):
        if not self.permission_manager.has_permission(PERM_R_PURCHASE_RETURN):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_R_PURCHASE_RETURN)
            return

        # Temporarily disable sorting
        self.purchase_return_table.setSortingEnabled(False)
        
        # Get Dates
        start_date = datetime.strptime(self.ui.start_date_purchase_return_list_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')
        end_date = datetime.strptime(self.ui.end_date_purchase_return_list_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')

        # Get search text if any
        search_text = self.ui.filter_purchase_return_list_input.text().strip()
        search_text = search_text if search_text != '' else None

        # Get all purchase return
        purchase_return_result = self.purchase_return_list_service.get_purchase_return_list(
            start_date = start_date.replace(hour=0, minute=0, second=0),
            end_date = end_date.replace(hour=23, minute=59, second=59),
            search_text=search_text
        )

        # Set purchase return data
        if purchase_return_result.success and purchase_return_result.data:
            self.set_purchase_return_table_data(purchase_return_result.data)


    # Event Listeners
    # ===============
    def on_purchase_return_selected(self):
        selected_rows = self.purchase_return_table.selectedItems()
        if selected_rows:
            self.detail_purchase_return_table.setSortingEnabled(False)
            # Get the first selected row
            row = selected_rows[1].row()
            self.current_selected_purchase_return_id = self.purchase_return_table.item(row, 1).text()
            
            dt_results = self.purchase_return_list_service.get_detail_purchase_return_by_id(self.current_selected_purchase_return_id)
            if dt_results.success:
                self.set_detail_purchase_return_table_data(dt_results.data)


    def filter_detail_purchase_return(self):
        search_text = self.ui.filter_detail_purchase_return_list_input.text().upper()
        for row in range(self.detail_purchase_return_table.rowCount()):
            match_found = False
            for col in range(self.detail_purchase_return_table.columnCount()):
                item = self.detail_purchase_return_table.item(row, col)
                if item and search_text in item.text().upper():
                    match_found = True
                    break
            self.detail_purchase_return_table.setRowHidden(row, not match_found)

    
    # Event Filters
    # ==============
    def closeEvent(self, event):
        """Override closeEvent to show home window when window is closed"""
        if self.home_window:
            self.home_window.show()
            self.home_window.raise_()
            self.home_window.activateWindow()
            
        event.accept()