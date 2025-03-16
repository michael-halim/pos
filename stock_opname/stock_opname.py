from PyQt6 import QtWidgets, uic, QtGui
from datetime import datetime

from stock_opname.services.stock_opname_services import StockOpnameService
from stock_opname.models.stock_opname_models import StockOpnameModel

from helper import format_number
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
from generals.permission_manager import PermissionManager


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

        # Init Tables
        self.stock_opname_table = self.ui.stock_opname_table

        # Connect Buttons
        self.ui.close_stock_opname_button.clicked.connect(lambda: self.close())
        self.ui.export_excel_stock_opname_button.clicked.connect(self.export_excel)
        self.ui.export_pdf_stock_opname_button.clicked.connect(self.export_pdf)

        # Connect filter products input
        self.ui.filter_products_stock_opname_input.textChanged.connect(self.show_stock_opname_data)

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
        
        self.show_stock_opname_data()


    def show(self):
        super().show()
        if not self.permission_manager.has_permission(PERM_R_STOCK_OPNAME):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_STOCK_OPNAME)
            return
        
        self.show_stock_opname_data()
   

    def showMaximized(self):
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_R_STOCK_OPNAME):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_STOCK_OPNAME)
            return
        
        self.show_stock_opname_data()


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
               current_stock,
               QtWidgets.QTableWidgetItem(stock_opname.unit),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.stock_opname_table.setItem(current_row, col, item)    

        self.stock_opname_table.setSortingEnabled(True)


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
