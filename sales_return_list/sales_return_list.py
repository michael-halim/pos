from PyQt6 import QtWidgets, uic
from datetime import datetime

from sales_return.sales_return import SalesReturnWindow

from sales_return_list.services.sales_return_list_services import SalesReturnListService
from sales_return_list.models.sales_return_list_models import SalesReturnListModel, DetailSalesReturnListModel

from helper import format_number, add_prefix
from generals.message_box import POSMessageBox
from generals.build import resource_path
from generals.fonts import POSFonts
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    PERM_R_SALES_RETURN, PERM_C_SALES_RETURN, 
    PERM_U_SALES_RETURN, PERM_D_SALES_RETURN, DATE_FORMAT_DDMMYYYY
) 
from generals.messages import (
    ERR, OK, ERR_PERM_R_SALES_RETURN, ERR_PERM_C_SALES_RETURN, 
    ERR_PERM_U_SALES_RETURN, ERR_PERM_D_SALES_RETURN,
    PERM_DENIED
)
from sales_return_list.translations import SALES_RETURN_LIST_TRANSLATIONS
from generals.language_manager import LanguageManager
from generals.permission_manager import PermissionManager


class SalesReturnListWindow(QtWidgets.QWidget):
    def __init__(self, home_window: None):
        super().__init__()

        self.home_window = home_window

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_SALES_RETURN):   
            return
        
        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/sales_return_list.ui'), self)

        # Init Services
        self.sales_return_list_service = SalesReturnListService()

        # Init Windows
        self.sales_return_window = SalesReturnWindow(home_window)

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(SALES_RETURN_LIST_TRANSLATIONS)
        
        # Connect Filter Sales Return
        self.ui.filter_sales_return_list_input.textChanged.connect(self.show_sales_return_data)
        self.ui.filter_detail_sales_return_list_input.textChanged.connect(self.filter_detail_sales_return)

        # Connect Buttons
        self.ui.find_sales_return_list_button.clicked.connect(self.show_sales_return_data)
        self.ui.edit_sales_return_button.clicked.connect(self.edit_sales_return)
        self.ui.delete_sales_return_button.clicked.connect(self.delete_sales_return)
        self.ui.create_sales_return_button.clicked.connect(self.create_sales_return)
        self.ui.close_sales_return_list_button.clicked.connect(lambda: self.close())

        # Init Tables
        self.sales_return_table = self.ui.sales_return_table
        self.detail_sales_return_table = self.ui.detail_sales_return_table

        # Connect table selection
        self.sales_return_table.itemSelectionChanged.connect(self.on_sales_return_selected)
        
        # Set date input
        self.ui.start_date_sales_return_list_input.setDate(datetime.now())
        self.ui.end_date_sales_return_list_input.setDate(datetime.now())

        self.ui.start_date_sales_return_list_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)
        self.ui.end_date_sales_return_list_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)

        # Add selected tracking
        self.current_selected_sku = None
     
        # Set selection behavior to select entire rows
        self.sales_return_table.setSelectionBehavior(SELECT_ROWS)
        self.sales_return_table.setSelectionMode(SINGLE_SELECTION)
        self.detail_sales_return_table.setSelectionBehavior(SELECT_ROWS)
        self.detail_sales_return_table.setSelectionMode(SINGLE_SELECTION)

        # Set wholesale sales return table to be read only
        self.sales_return_table.setEditTriggers(NO_EDIT_TRIGGERS)
        self.detail_sales_return_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.sales_return_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.sales_return_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.detail_sales_return_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.detail_sales_return_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        # Show data for both tables
        self.show_sales_return_data()


    # Overrides
    # ===============
    def showEvent(self, event):
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_R_SALES_RETURN):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_R_SALES_RETURN)
            return

        # Set window title
        if self.permission_manager.get_username().lower() not in self.windowTitle().lower():
            self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username())

        # Translate Widget Text
        self.language_manager.translate_widget_text(self)

        self.sales_return_table_headers = ['Date', 'Sales Return #', 'Customer Name', 'Total', 'Remarks']
        self.detail_sales_return_table_headers = ['SKU', 'Product Name', 'Price', 'Qty', 'Unit', 'Subtotal']

        if self.language_manager.get_current_language() == 'id':    
            self.sales_return_table_headers = ['Tanggal', 'ID Return Penjualan', 'Nama Customer', 'Total', 'Keterangan']
            self.detail_sales_return_table_headers = ['Kode Barang', 'Nama Produk', 'Harga', 'Qty', 'Satuan', 'Subtotal']

        self.language_manager.translate_table_headers(self.ui.sales_return_table, self.sales_return_table_headers)
        self.language_manager.translate_table_headers(self.ui.detail_sales_return_table, self.detail_sales_return_table_headers)


        # Refresh the data
        self.show_sales_return_data()


    def show(self):
        super().show()
        if not self.permission_manager.has_permission(PERM_R_SALES_RETURN):
            self.close()
            return

        # Refresh the data
        self.show_sales_return_data() 


    def showMaximized(self):
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_R_SALES_RETURN):
            self.close()
            return

        # Refresh the data
        self.show_sales_return_data()


    def create_sales_return(self):
        if not self.permission_manager.has_permission(PERM_C_SALES_RETURN):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_C_SALES_RETURN)
            return

        self.sales_return_window.showMaximized()


    def edit_sales_return(self):
        if not self.permission_manager.has_permission(PERM_U_SALES_RETURN):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_U_SALES_RETURN)
            return

        selected_rows = self.sales_return_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title=ERR, message="Please select a sales return to edit")
            return
        
        row = selected_rows[0].row()
        sales_return_id = self.sales_return_table.item(row, 1).text()

        self.sales_return_window.set_sales_return_by_id(sales_return_id)
        self.sales_return_window.showMaximized()


    def delete_sales_return(self):
        if not self.permission_manager.has_permission(PERM_D_SALES_RETURN):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_D_SALES_RETURN)
            return

        selected_rows = self.sales_return_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title=ERR, message="Please select a sales return to delete")
            return
        
        row = selected_rows[0].row()
        sales_return_id = self.sales_return_table.item(row, 1).text()

        confirm = POSMessageBox.confirm(
                    self, title='Confirm Deletion', 
                    message=f'Are you sure you want to delete {sales_return_id} ?')

        if confirm:
            result = self.sales_return_list_service.delete_sales_return_by_id(sales_return_id)
            if result.success:
                POSMessageBox.info(self, title=OK, message=result.message)

                # Just refresh the data directly
                self.show_sales_return_data()

            else:
                POSMessageBox.error(self, title=ERR, message=result.message)


    # Setters
    # ===============
    def set_sales_return_table_data(self, data: list[SalesReturnListModel]):
        # Clear the table
        self.sales_return_table.setRowCount(0)
        total_sales_return = 0
        for sales_return in data:
            current_row = self.sales_return_table.rowCount()
            self.sales_return_table.insertRow(current_row)

            # Convert created_at string to datetime and format
            created_at_dt = datetime.strptime(sales_return.created_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = created_at_dt.strftime('%d %b %y %H:%M')

            table_items =  [ 
                QtWidgets.QTableWidgetItem(formatted_date),
                QtWidgets.QTableWidgetItem(sales_return.sales_return_id),
                QtWidgets.QTableWidgetItem(sales_return.customer_name),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(sales_return.total_amount))),
                QtWidgets.QTableWidgetItem(sales_return.remarks),
            ]

            total_sales_return += sales_return.total_amount

            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.sales_return_table.setItem(current_row, col, item)

        self.ui.total_sales_return_input.setText(add_prefix(format_number(total_sales_return)))

        self.sales_return_table.setSortingEnabled(True)


    def set_detail_sales_return_table_data(self, data: list[DetailSalesReturnListModel]):
        # Clear the table
        self.detail_sales_return_table.setRowCount(0)

        for detail_sales_return in data:
            current_row = self.detail_sales_return_table.rowCount()
            self.detail_sales_return_table.insertRow(current_row)


            table_items =  [ 
                QtWidgets.QTableWidgetItem(detail_sales_return.sku),
                QtWidgets.QTableWidgetItem(detail_sales_return.product_name),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(detail_sales_return.price))),
                QtWidgets.QTableWidgetItem(format_number(detail_sales_return.qty)),
                QtWidgets.QTableWidgetItem(detail_sales_return.unit),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(detail_sales_return.subtotal)))
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.detail_sales_return_table.setItem(current_row, col, item)
        
        self.detail_sales_return_table.setSortingEnabled(True)
 

    # Shows
    # ===============
    def show_sales_return_data(self):
        if not self.permission_manager.has_permission(PERM_R_SALES_RETURN):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_R_SALES_RETURN)
            return

        # Temporarily disable sorting
        self.sales_return_table.setSortingEnabled(False)
        
        # Get Dates
        start_date = datetime.strptime(self.ui.start_date_sales_return_list_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')
        end_date = datetime.strptime(self.ui.end_date_sales_return_list_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')

        # Get search text if any
        search_text = self.ui.filter_sales_return_list_input.text().strip()
        search_text = search_text if search_text != '' else None

        # Get all sales return
        sales_return_result = self.sales_return_list_service.get_sales_return_list(
            start_date = start_date.replace(hour=0, minute=0, second=0),
            end_date = end_date.replace(hour=23, minute=59, second=59),
            search_text=search_text
        )

        # Set sales return data
        if sales_return_result.success and sales_return_result.data:
            self.set_sales_return_table_data(sales_return_result.data)


    # Event Listeners
    # ===============
    def on_sales_return_selected(self):
        selected_rows = self.sales_return_table.selectedItems()
        if selected_rows:
            self.detail_sales_return_table.setSortingEnabled(False)
            # Get the first selected row
            row = selected_rows[1].row()
            self.current_selected_sales_return_id = self.sales_return_table.item(row, 1).text()
            
            dt_results = self.sales_return_list_service.get_detail_sales_return_by_id(self.current_selected_sales_return_id)
            if dt_results.success:
                self.set_detail_sales_return_table_data(dt_results.data)


    def filter_detail_sales_return(self):
        search_text = self.ui.filter_detail_sales_return_list_input.text().upper()
        for row in range(self.detail_sales_return_table.rowCount()):
            match_found = False
            for col in range(self.detail_sales_return_table.columnCount()):
                item = self.detail_sales_return_table.item(row, col)
                if item and search_text in item.text().upper():
                    match_found = True
                    break
            self.detail_sales_return_table.setRowHidden(row, not match_found)

    
    # Event Filters
    # ==============
    def closeEvent(self, event):
        """Override closeEvent to show home window when window is closed"""
        if self.home_window:
            self.home_window.show()
            self.home_window.raise_()
            self.home_window.activateWindow()
            
        event.accept()
