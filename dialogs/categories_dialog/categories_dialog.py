from PyQt6 import QtWidgets, uic, QtCore

from helper import format_number, add_prefix
from generals.fonts import POSFonts
from generals.build import resource_path
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION
from dialogs.categories_dialog.models.categories_dialog_models import CategoriesDialogModel
from dialogs.categories_dialog.services.categories_dialog_services import CategoriesDialogService
from datetime import datetime

class CategoriesDialogWindow(QtWidgets.QDialog):
    # Add signal to communicate with main window
    category_selected = QtCore.pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()

        # Init Services
        self.categories_dialog_service = CategoriesDialogService()

        self.ui = uic.loadUi(resource_path('ui/categories_dialog.ui'), self)

        # Init Table
        self.categories_dialog_table = self.ui.categories_dialog_table
        self.categories_dialog_table.setSortingEnabled(True)
        
        # Init Button
        self.ui.add_categories_dialog_button.clicked.connect(self.send_category_data)
        self.ui.close_categories_dialog_button.clicked.connect(lambda: self.close())
        
        # Connect search input to filter function
        self.ui.filter_categories_dialog_input.textChanged.connect(self.show_categories_data)

        # Set selection behavior to select entire rows
        self.categories_dialog_table.setSelectionBehavior(SELECT_ROWS)
        self.categories_dialog_table.setSelectionMode(SINGLE_SELECTION)

        # Set table properties
        self.categories_dialog_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.categories_dialog_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        self.show_categories_data()


    # Shows
    # ===============
    def show_categories_data(self):
        search_text = self.ui.filter_categories_dialog_input.text().strip()
        search_text = search_text.lower() if search_text else None

        categories_dialog_result = self.categories_dialog_service.get_categories(search_text)

        self.set_categories_table_data(categories_dialog_result.data)

    # Overrides
    # ===============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        # Refresh the data
        self.show_categories_data()


    def show(self):
        """Override show to ensure data is refreshed"""
        super().show()
        # Refresh the data
        self.show_categories_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        # Refresh the data
        self.show_categories_data()


    # Setters
    # ===============
    def set_categories_table_data(self, data: list[CategoriesDialogModel]):
        # Clear the table
        self.categories_dialog_table.setRowCount(0)

        for category in data:
            current_row = self.categories_dialog_table.rowCount()
            self.categories_dialog_table.insertRow(current_row)

            table_items =  [ 
                QtWidgets.QTableWidgetItem(str(category.category_id)),
                QtWidgets.QTableWidgetItem(category.category_name),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.categories_dialog_table.setItem(current_row, col, item)


    # Signal Handlers
    # ===============
    def send_category_data(self):
        selected_rows = self.categories_dialog_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            
            # Create dictionary with category details
            category_data = {
                'category_id': self.categories_dialog_table.item(row, 0).text(),
            }
            
            # Emit signal with category data
            self.category_selected.emit(category_data)
            self.close()


    def set_filter(self, search_text: str):
        """Pre-fill the search filter"""
        self.ui.filter_categories_dialog_input.setText(search_text)
        # Optionally trigger the filter
        self.filter_categories()


    def filter_categories(self):
        search_text = self.ui.filter_categories_dialog_input.text().lower()
        for row in range(self.categories_dialog_table.rowCount()):
            match_found = False
            for col in range(self.categories_dialog_table.columnCount()):
                item = self.categories_dialog_table.item(row, col)
                if item and search_text in item.text().lower():
                    match_found = True
                    break
            self.categories_dialog_table.setRowHidden(row, not match_found)
