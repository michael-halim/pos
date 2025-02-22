from PyQt6 import QtWidgets, uic
from datetime import datetime

from helper import format_number, add_prefix, remove_non_digit

from dialogs.products_dialog import ProductsDialogWindow

from purchasing_list.services.purchasing_list_services import PurchasingListService
from purchasing_list.models.purchasing_list_models import PurchasingListModel, DetailPurchasingModel

from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS, DATE_FORMAT_DDMMYYYY, DATE_EDIT_NO_BUTTONS

from dialogs.suppliers_dialog.suppliers_dialog import SuppliersDialogWindow
from dialogs.master_stock_dialog.master_stock_dialog import MasterStockDialogWindow
from dialogs.price_unit_dialog.price_unit_dialog import PriceUnitDialogWindow
from generals.build import resource_path

class PurchasingListWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.purchasing_list_service = PurchasingListService()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/purchasing_list.ui'), self)


        # Connect Filter Purchasing
        self.ui.filter_purchasing_list_input.textChanged.connect(self.show_purchasing_data)
        self.ui.filter_detail_purchasing_list_input.textChanged.connect(self.filter_detail_purchasing)

        # Connect Buttons
        self.ui.find_purchasing_list_button.clicked.connect(self.show_purchasing_data)

        # Init Tables
        self.purchasing_table = self.ui.purchasing_table
        self.detail_purchasing_table = self.ui.detail_purchasing_table

        self.purchasing_table.setSortingEnabled(True)
        self.detail_purchasing_table.setSortingEnabled(True)

        # Connect table selection
        self.purchasing_table.itemSelectionChanged.connect(self.on_purchasing_selected)
        
        # Set date input
        self.ui.start_date_purchasing_list_input.setDate(datetime.now())
        self.ui.end_date_purchasing_list_input.setDate(datetime.now())

        self.ui.start_date_purchasing_list_input.setDisplayFormat("dd/MM/yyyy")
        self.ui.end_date_purchasing_list_input.setDisplayFormat("dd/MM/yyyy")

        # Add selected tracking
        self.current_selected_sku = None
     
        # Set selection behavior to select entire rows
        self.purchasing_table.setSelectionBehavior(SELECT_ROWS)
        self.purchasing_table.setSelectionMode(SINGLE_SELECTION)
        self.detail_purchasing_table.setSelectionBehavior(SELECT_ROWS)
        self.detail_purchasing_table.setSelectionMode(SINGLE_SELECTION)

        # Set wholesale purchasing table to be read only
        self.purchasing_table.setEditTriggers(NO_EDIT_TRIGGERS)
        self.detail_purchasing_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.purchasing_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.purchasing_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.detail_purchasing_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.detail_purchasing_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        # Show data for both tables
        self.show_purchasing_data()


    # Setters
    # ===============
    def set_purchasing_table_data(self, data: list[PurchasingListModel]):
        for purchasing in data:
            current_row = self.purchasing_table.rowCount()
            self.purchasing_table.insertRow(current_row)

            # Convert created_at string to datetime and format
            created_at_dt = datetime.strptime(purchasing.created_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = created_at_dt.strftime('%d %b %y %H:%M')

            table_items =  [ 
                QtWidgets.QTableWidgetItem(formatted_date),
                QtWidgets.QTableWidgetItem(purchasing.purchasing_id),
                QtWidgets.QTableWidgetItem(purchasing.supplier_name),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(purchasing.total_amount))),
                QtWidgets.QTableWidgetItem(purchasing.remarks),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.purchasing_table.setItem(current_row, col, item)


    def set_detail_purchasing_table_data(self, data: list[DetailPurchasingModel]):
        # Clear the table
        self.detail_purchasing_table.setRowCount(0)

        for detail_purchasing in data:
            current_row = self.detail_purchasing_table.rowCount()
            self.detail_purchasing_table.insertRow(current_row)


            table_items =  [ 
                QtWidgets.QTableWidgetItem(detail_purchasing.sku),
                QtWidgets.QTableWidgetItem(detail_purchasing.product_name),
                QtWidgets.QTableWidgetItem(format_number(detail_purchasing.price)),
                QtWidgets.QTableWidgetItem(format_number(detail_purchasing.qty)),
                QtWidgets.QTableWidgetItem(detail_purchasing.unit),
                QtWidgets.QTableWidgetItem(format_number(detail_purchasing.discount_pct)),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(detail_purchasing.discount_rp))),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(detail_purchasing.subtotal)))
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.detail_purchasing_table.setItem(current_row, col, item)



    # Getters
    # ===============

    
    # Signal Handlers
    # ===============

    # Calculate
    # ===============

    # Shows
    # ===============
    def show_purchasing_data(self):
        # Temporarily disable sorting
        self.purchasing_table.setSortingEnabled(False)
        
        # Clear the table
        self.purchasing_table.setRowCount(0)
        
        # Get Dates
        start_date = datetime.strptime(self.ui.start_date_purchasing_list_input.date().toString('dd/MM/yyyy'), '%d/%m/%Y')
        end_date = datetime.strptime(self.ui.end_date_purchasing_list_input.date().toString('dd/MM/yyyy'), '%d/%m/%Y')

        # Get search text if any
        search_text = self.ui.filter_purchasing_list_input.text().strip()
        search_text = search_text if search_text != '' else None

        # Get all purchasing
        purchasing_result = self.purchasing_list_service.get_purchasing_list(
            start_date = start_date.replace(hour=0, minute=0, second=0),
            end_date = end_date.replace(hour=23, minute=59, second=59),
            search_text=search_text
        )

        # Set purchasing data
        if purchasing_result.success and purchasing_result.data:
            self.set_purchasing_table_data(purchasing_result.data)
        
        # Enable sorting
        self.purchasing_table.setSortingEnabled(True)


    # Event Listeners
    # ===============
    def on_purchasing_selected(self):
        selected_rows = self.purchasing_table.selectedItems()
        if selected_rows:
            # Get the first selected row
            row = selected_rows[1].row()
            self.current_selected_purchasing_id = self.purchasing_table.item(row, 1).text()
            
            dt_results = self.purchasing_list_service.get_detail_purchasing_by_id(self.current_selected_purchasing_id)
            if dt_results.success:
                self.set_detail_purchasing_table_data(dt_results.data)


    def filter_detail_purchasing(self):
        pass
