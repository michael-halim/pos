from PyQt6 import QtWidgets, uic, QtGui
from datetime import datetime

from stock_opname.services.stock_opname_services import StockOpnameService
from stock_opname.models.stock_opname_models import StockOpnameModel, EditStockOpnameModel

from helper import format_number, add_prefix
from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.build import resource_path
from exports.export_service import ExportService
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    PERM_R_STOCK_OPNAME, PERM_E_STOCK_OPNAME
) 
from generals.messages import (
    ERR, OK, ERR_PERM_R_STOCK_OPNAME, ERR_PERM_E_STOCK_OPNAME, PERM_DENIED
)
from stock_opname.translations import STOCK_OPNAME_TRANSLATIONS
from generals.permission_manager import PermissionManager
from generals.language_manager import LanguageManager


class StockOpnameWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_STOCK_OPNAME):
            return

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/stock_opname.ui'), self)

        # Init Services
        self.stock_opname_service = StockOpnameService()
        self.export_service = ExportService()

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(STOCK_OPNAME_TRANSLATIONS)

        # Init Tables
        self.stock_opname_table = self.ui.stock_opname_table

        # Connect Buttons
        self.ui.submit_stock_opname_button.clicked.connect(self.submit_stock_opname)
        self.ui.close_stock_opname_button.clicked.connect(lambda: self.close())
        self.ui.export_excel_stock_opname_button.clicked.connect(self.export_excel)
        self.ui.export_pdf_stock_opname_button.clicked.connect(self.export_pdf)

        # Connect filter products input
        self.ui.filter_products_stock_opname_input.textChanged.connect(self.show_stock_opname_data)

        # Connect table selection
        self.stock_opname_table.itemSelectionChanged.connect(self.on_stock_opname_table_selected)

        # Set selection behavior to select entire rows
        self.stock_opname_table.setSelectionBehavior(SELECT_ROWS)
        self.stock_opname_table.setSelectionMode(SINGLE_SELECTION)

        # Set wholesale purchasing table to be read only
        self.stock_opname_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.stock_opname_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.stock_opname_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        # Show data for both tables
        self.show_stock_opname_data()


    # Overrides
    # ===============
    def showEvent(self, event):
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_R_STOCK_OPNAME):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_STOCK_OPNAME)
            self.close()
            return
        
        # Translate Widget Text
        self.language_manager.translate_widget_text(self)

        self.stock_opname_headers = ['SKU', 'Product Name', 'Price', 'Qty', 'Unit']
        if self.language_manager.get_current_language() == 'id':
            self.stock_opname_headers = ['Kode Barang', 'Nama Produk', 'Harga', 'Qty', 'Satuan']

        self.language_manager.translate_table_headers(self.stock_opname_table, self.stock_opname_headers)

        self.show_stock_opname_data()


    def show(self):
        super().show()
        if not self.permission_manager.has_permission(PERM_R_STOCK_OPNAME):
            self.close()
        
        self.show_stock_opname_data()
   

    def showMaximized(self):
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_R_STOCK_OPNAME):
            self.close()
        
        self.show_stock_opname_data()


    def submit_stock_opname(self):
        sku = self.ui.sku_stock_opname_input.text()
        product_name = self.ui.product_name_stock_opname_input.text()
        original_stock = self.ui.original_stock_stock_opname_input.text()
        final_stock = self.ui.final_stock_stock_opname_input.text()
        price = self.ui.price_stock_opname_input.text()

        edit_stock_opname_data = EditStockOpnameModel(
            sku=sku,
            product_name=product_name,
            price=price,
            original_stock=original_stock,
            final_stock=final_stock
        )

        stock_opname_result = self.stock_opname_service.create_stock_opname(edit_stock_opname_data)
        if stock_opname_result.success:

            POSMessageBox.info(self, title=OK, message=stock_opname_result.message)
            self.clear_edit_stock_opname_data()
            self.show_stock_opname_data()

        else:
            POSMessageBox.error(self, title=ERR, message=stock_opname_result.message)


    # Shows
    # ===============
    def show_stock_opname_data(self):
        if not self.permission_manager.has_permission(PERM_R_STOCK_OPNAME):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_STOCK_OPNAME)
            return
        
        self.stock_opname_table.setSortingEnabled(False)

        search_text = self.ui.filter_products_stock_opname_input.text().strip()
        search_text = search_text.lower() if search_text else None

        stock_opname_result = self.stock_opname_service.get_stock_opname(search_text)

        if not stock_opname_result.success:
            POSMessageBox.warning(self, title=ERR, message=stock_opname_result.message)
            return

        self.set_stock_opname_table_data(stock_opname_result.data)

    
    # Setters
    # ===============
    def set_stock_opname_table_data(self, data: list[StockOpnameModel]):
        # Clear the table
        self.stock_opname_table.setRowCount(0)

        for stock_opname in data:
            current_row = self.stock_opname_table.rowCount()
            self.stock_opname_table.insertRow(current_row)


            # Change stock color if negative
            current_stock = QtWidgets.QTableWidgetItem(str(stock_opname.qty))
            if stock_opname.qty < 0:
                current_stock = QtWidgets.QTableWidgetItem(f'-{format_number(str(stock_opname.qty))}')
                current_stock.setForeground(QtGui.QColor(255, 0, 0))


            table_items =  [ 
               QtWidgets.QTableWidgetItem(stock_opname.sku),
               QtWidgets.QTableWidgetItem(stock_opname.product_name),
               QtWidgets.QTableWidgetItem(add_prefix(format_number(str(stock_opname.price)))),
               current_stock,
               QtWidgets.QTableWidgetItem(stock_opname.unit),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.stock_opname_table.setItem(current_row, col, item)    

        self.stock_opname_table.setSortingEnabled(True)


    # Event Listeners
    # ===============
    def on_stock_opname_table_selected(self):
        selected_items = self.stock_opname_table.selectedItems()
        if not selected_items:
            return
        
        selected_item = selected_items[0]
        selected_row = selected_item.row()
        selected_sku = self.stock_opname_table.item(selected_row, 0).text()
        selected_product_name = self.stock_opname_table.item(selected_row, 1).text()
        selected_price = self.stock_opname_table.item(selected_row, 2).text()
        selected_stock = self.stock_opname_table.item(selected_row, 3).text()

        self.ui.sku_stock_opname_input.setText(selected_sku)
        self.ui.product_name_stock_opname_input.setText(selected_product_name)
        self.ui.price_stock_opname_input.setText(selected_price)
        self.ui.original_stock_stock_opname_input.setText(selected_stock)

    # Exports Excel
    # ===============
    def export_excel(self):
        """Export stock opname data to Excel"""

        if not self.permission_manager.has_permission(PERM_E_STOCK_OPNAME):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_E_STOCK_OPNAME)
            return
        
        # Get save file location from user
        file_name = f"stock_opname_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 
            "Save Excel File",
            file_name, 
            "Excel Files (*.xlsx)"
        )

        # If User cancelled
        if not file_path:  
            return
            
        # Add .xlsx extension if not present
        if not file_path.endswith('.xlsx'):
            file_path += '.xlsx'

        # Export
        stock_opname_result = self.stock_opname_service.get_stock_opname()
        self.stock_opname_service.export_excel(stock_opname_result.data, file_path, 
                                               self.on_complete_export_excel, self.on_error_export_excel, self.on_progress_export_excel)


    # Exports Excel Callbacks
    # ===============
    def on_complete_export_excel(self, export_result):
        if export_result.success:
            POSMessageBox.info(self, title=OK, message=export_result.message)
        else:
            POSMessageBox.error(self, title=ERR, message=export_result.message)


    def on_error_export_excel(self, error):
        POSMessageBox.error(self, title=ERR, message=error)


    def on_progress_export_excel(self, progress: int):
        print(f"Progress: {progress}")


    # Exports PDF
    # ===============
    def export_pdf(self):
        """Export stock opname data to PDF"""

        if not self.permission_manager.has_permission(PERM_E_STOCK_OPNAME):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_E_STOCK_OPNAME)
            return
        
        # Get save file location from user
        file_name = f"stock_opname_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 
            "Save PDF File",
            file_name, 
            "PDF Files (*.pdf)"
        )
        
        # If User cancelled
        if not file_path:  
            return
            
        # Add .pdf extension if not present
        if not file_path.endswith('.pdf'):
            file_path += '.pdf'

        stock_opname_result = self.stock_opname_service.get_stock_opname()
        self.stock_opname_service.export_pdf(stock_opname_result.data, file_path, 
                                             self.on_complete_export_pdf, self.on_error_export_pdf, self.on_progress_export_pdf)


    # Export PDF Callbacks 
    # ===============
    def on_complete_export_pdf(self, export_result):
        if export_result.success:
            POSMessageBox.info(self, title=OK, message=export_result.message)

        else:
            POSMessageBox.error(self, title=ERR, message=export_result.message)


    def on_error_export_pdf(self, error):
        POSMessageBox.error(self, title=ERR, message=error)


    def on_progress_export_pdf(self, progress: int):
        print(f"Progress: {progress}")


    # Clears
    # ===============
    def clear_edit_stock_opname_data(self):
        self.ui.sku_stock_opname_input.clear()
        self.ui.product_name_stock_opname_input.clear()
        self.ui.price_stock_opname_input.clear()
        self.ui.original_stock_stock_opname_input.clear()
        self.ui.final_stock_stock_opname_input.clear()
