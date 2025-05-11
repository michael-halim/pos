from PyQt6 import QtWidgets, uic, QtGui
from datetime import datetime, timedelta

from dialogs.edit_stock_opname_dialog.edit_stock_opname_dialog import EditStockOpnameDialogWindow
from stock_opname_list.services.stock_opname_list_services import StockOpnameListService
from stock_opname_list.models.stock_opname_list_models import StockOpnameListModel
from stock_opname.models.stock_opname_models import EditStockOpnameModel
from stock_opname.stock_opname import StockOpnameWindow

from helper import format_number, add_prefix
from generals.message_box import POSMessageBox
from generals.build import resource_path
from generals.fonts import POSFonts
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    PERM_R_STOCK_OPNAME, PERM_C_STOCK_OPNAME, PERM_U_STOCK_OPNAME, 
    PERM_D_STOCK_OPNAME, DATE_FORMAT_DDMMYYYY
) 
from generals.messages import (
    ERR, OK, ERR_PERM_R_STOCK_OPNAME, 
    ERR_PERM_C_STOCK_OPNAME, ERR_PERM_U_STOCK_OPNAME, 
    ERR_PERM_D_STOCK_OPNAME, PERM_DENIED, CONFIRM
)
from stock_opname_list.translations import STOCK_OPNAME_LIST_TRANSLATIONS
from generals.permission_manager import PermissionManager
from generals.language_manager import LanguageManager


class StockOpnameListWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_STOCK_OPNAME):
            return
        
        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/stock_opname_list.ui'), self)

        # Init Services
        self.stock_opname_list_service = StockOpnameListService()

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(STOCK_OPNAME_LIST_TRANSLATIONS)

        # Init Stock Opname Window
        self.stock_opname_window = StockOpnameWindow()
        self.edit_stock_opname_dialog = EditStockOpnameDialogWindow()

        # Connect Buttons
        self.ui.create_stock_opname_button.clicked.connect(self.create_stock_opname)
        self.ui.edit_stock_opname_button.clicked.connect(self.edit_stock_opname)
        self.ui.delete_stock_opname_button.clicked.connect(self.delete_stock_opname)
        self.ui.close_stock_opname_list_button.clicked.connect(lambda: self.close())

        # Connect Filter Transactions
        self.ui.filter_stock_opname_list_input.textChanged.connect(self.show_stock_opname_data)
        self.ui.find_stock_opname_list_button.clicked.connect(self.show_stock_opname_data)

        # Set date input
        self.ui.start_date_stock_opname_list_input.setDate(datetime.now() - timedelta(days=1))
        self.ui.end_date_stock_opname_list_input.setDate(datetime.now())

        self.ui.start_date_stock_opname_list_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)
        self.ui.end_date_stock_opname_list_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)

        # Set selection behavior to select entire rows
        self.stock_opname_list_table.setSelectionBehavior(SELECT_ROWS)
        self.stock_opname_list_table.setSelectionMode(SINGLE_SELECTION)

        # Set stock opname table to be read only
        self.stock_opname_list_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.stock_opname_list_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.stock_opname_list_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        
        # Show data for both tables
        self.show_stock_opname_data()


    # Overrides
    # ==============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)

        if not self.permission_manager.has_permission(PERM_R_STOCK_OPNAME):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_R_STOCK_OPNAME)
            self.close()
            return
        
        # Set window title
        if self.permission_manager.get_username().lower() not in self.windowTitle().lower():
            self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username())

        # Translate Widget Text
        self.language_manager.translate_widget_text(self)

        self.stock_opname_headers = ['SO #', 'Created At', 'SKU', 'Product Name', 'Price', 'Original Stock', 'Opname Stock', 'Final Stock' ]
        if self.language_manager.get_current_language() == 'id':
            self.stock_opname_headers = ['Id Stock Opname', 'Tanggal', 'Kode Barang', 'Nama Produk', 'Harga', 'Stok Awal', 'Opname', 'Stok Akhir' ]

        self.language_manager.translate_table_headers(self.ui.stock_opname_list_table, self.stock_opname_headers)

        # Refresh the data
        self.show_stock_opname_data()


    def show(self):
        """Override show to refresh data when window is shown"""
        super().show()

        if not self.permission_manager.has_permission(PERM_R_STOCK_OPNAME):
            self.close()
            return
        
        # Refresh the data
        self.show_stock_opname_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()

        if not self.permission_manager.has_permission(PERM_R_STOCK_OPNAME):
            self.close()
            return
        
        # Refresh the data
        self.show_stock_opname_data()


    def create_stock_opname(self):
        if not self.permission_manager.has_permission(PERM_C_STOCK_OPNAME):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_C_STOCK_OPNAME)
            return
        
        self.stock_opname_window.showMaximized()


    def edit_stock_opname(self):
        if not self.permission_manager.has_permission(PERM_U_STOCK_OPNAME):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_U_STOCK_OPNAME)
            return
        
        # Check if any stock opname is selected
        if not self.stock_opname_list_table.selectedItems():
            POSMessageBox.warning(self, title=ERR, message="Please select a stock opname to edit")
            return
        
        # Get selected row
        selected_rows = self.stock_opname_list_table.selectedItems()
        row = selected_rows[0].row()

        # Get stock opname id
        stock_opname_id = self.stock_opname_list_table.item(row, 0).text()

        # Get selected stock opname data
        selected_stock_opname_data = self.get_selected_stock_opname_data()

        self.edit_stock_opname_dialog.set_stock_opname(stock_opname_id, selected_stock_opname_data)
        self.edit_stock_opname_dialog.show()


    def delete_stock_opname(self):
        if not self.permission_manager.has_permission(PERM_D_STOCK_OPNAME):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_D_STOCK_OPNAME)
            return
        
        selected_rows = self.stock_opname_list_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title=ERR, message="Please select a stock opname to delete")
            return
        
        row = selected_rows[0].row()
        stock_opname_id = self.stock_opname_list_table.item(row, 0).text()

        confirm = POSMessageBox.confirm(
            self, title=CONFIRM, 
            message=f'Are you sure you want to delete stock opname SO#{stock_opname_id} ?'
        )

        if confirm:
            result = self.stock_opname_list_service.delete_stock_opname_by_id(stock_opname_id)
            if result.success:
                POSMessageBox.info(self, title=OK, message=result.message)

                # Just refresh the data directly
                self.show_stock_opname_data()

            else:
                POSMessageBox.error(self, title=ERR, message=result.message)


    # Shows
    # ==============
    def show_stock_opname_data(self):
        if not self.permission_manager.has_permission(PERM_R_STOCK_OPNAME):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_STOCK_OPNAME)
            return
        
        # Temporarily disable sorting
        self.stock_opname_list_table.setSortingEnabled(False)
        
        # Get Dates
        start_date = datetime.strptime(self.ui.start_date_stock_opname_list_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')
        end_date = datetime.strptime(self.ui.end_date_stock_opname_list_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')

        # Get search text if any
        search_text = self.ui.filter_stock_opname_list_input.text().strip()
        search_text = search_text if search_text != '' else None

        # Get all transactions
        stock_opname_result = self.stock_opname_list_service.get_stock_opname_list(
            start_date = start_date.replace(hour=0, minute=0, second=0),
            end_date = end_date.replace(hour=23, minute=59, second=59),
            search_text=search_text
        )

        if not stock_opname_result.success:
            POSMessageBox.error(self, title=ERR, message=stock_opname_result.message)
            return
        
        # Set stock opname table data
        self.set_stock_opname_list_table_data(stock_opname_result.data)
        

    # Setters
    # ==============
    def set_stock_opname_list_table_data(self, data: list[StockOpnameListModel]):
        # Clear the table
        self.stock_opname_list_table.setRowCount(0)

        for stock_opname in data:
            current_row = self.stock_opname_list_table.rowCount()
            self.stock_opname_list_table.insertRow(current_row)

            # Convert created_at string to datetime and format
            created_at_dt = datetime.strptime(stock_opname.created_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = created_at_dt.strftime('%d %b %y %H:%M:%S')

            opname_stock = QtWidgets.QTableWidgetItem(str(stock_opname.opname_stock))
            if stock_opname.opname_stock < 0:
                opname_stock = QtWidgets.QTableWidgetItem(f'-{format_number(str(stock_opname.opname_stock))}')
                opname_stock.setForeground(QtGui.QColor(255, 0, 0))

            table_items =  [ 
                QtWidgets.QTableWidgetItem(str(stock_opname.stock_opname_id)),
                QtWidgets.QTableWidgetItem(formatted_date),
                QtWidgets.QTableWidgetItem(stock_opname.sku),
                QtWidgets.QTableWidgetItem(stock_opname.product_name),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(stock_opname.price))),
                QtWidgets.QTableWidgetItem(format_number(stock_opname.original_stock)),
                opname_stock,
                QtWidgets.QTableWidgetItem(format_number(stock_opname.final_stock))
            ]

            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.stock_opname_list_table.setItem(current_row, col, item)

        self.stock_opname_list_table.setSortingEnabled(True)


    # Getters
    # ==============
    def get_selected_stock_opname_data(self) -> EditStockOpnameModel:
        if not self.stock_opname_list_table.selectedItems():
            POSMessageBox.warning(self, title=ERR, message="Please select a stock opname to edit")
            return
        
        selected_rows = self.stock_opname_list_table.selectedItems()
        row = selected_rows[0].row()

        return EditStockOpnameModel(
            sku=self.stock_opname_list_table.item(row, 2).text(),
            product_name=self.stock_opname_list_table.item(row, 3).text(),
            price=self.stock_opname_list_table.item(row, 4).text(),
            original_stock=self.stock_opname_list_table.item(row, 5).text(),
            final_stock=self.stock_opname_list_table.item(row, 7).text()
        )
