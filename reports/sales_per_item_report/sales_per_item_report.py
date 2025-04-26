from PyQt6 import QtWidgets, uic
from datetime import datetime, timedelta

from reports.sales_per_item_report.services.sales_per_item_report_services import SalesPerItemReportService
from reports.sales_per_item_report.models.sales_per_item_report_models import SalesPerItemReportModel
from dialogs.products_dialog.products_dialog import ProductsDialogWindow

from helper import format_number, add_prefix
from generals.build import resource_path
from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import ( 
    RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, BACKOFFICE_ID, CASHIER_ID,
    PERM_R_SALES_PER_ITEM_REPORT, DATE_FORMAT_DDMMYYYY
)
from generals.messages import (
    ERR_PERM_R_SALES_PER_ITEM_REPORT, PERM_DENIED
)
from generals.permission_manager import PermissionManager


class SalesPerItemReportWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_SALES_PER_ITEM_REPORT):
            return

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/sales_per_item_report.ui'), self)

        # Init Dialog
        self.products_dialog = ProductsDialogWindow()

        # Handle product selected from dialog
        self.products_dialog.product_selected.connect(self.handle_product_selected)

        # Init Services
        self.sales_per_item_report_service = SalesPerItemReportService()

        # Init Buttons
        self.ui.find_sales_per_item_button.clicked.connect(self.show_sales_per_item_data)
        self.ui.find_sku_sales_per_item_button.clicked.connect(lambda: self.products_dialog.show())
        self.ui.close_button.clicked.connect(lambda: self.close())
        
        # Connect return pressed signal
        self.ui.sku_sales_per_item_input.returnPressed.connect(self.on_handle_sku_enter)

        # Set date input
        self.ui.start_date_sales_per_item_input.setDate(datetime.now() - timedelta(days=1))
        self.ui.end_date_sales_per_item_input.setDate(datetime.now())

        self.ui.start_date_sales_per_item_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)
        self.ui.end_date_sales_per_item_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)

        # Set selection behavior to select entire rows
        self.sales_per_item_table.setSelectionBehavior(SELECT_ROWS)
        self.sales_per_item_table.setSelectionMode(SINGLE_SELECTION)

        # Set sales per item table to be read only
        self.sales_per_item_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.sales_per_item_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.sales_per_item_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)



    # Overrides
    # ==============
    def show(self):
        """Override show to refresh data when window is shown"""
        super().show()
        if not self.permission_manager.has_permission(PERM_R_SALES_PER_ITEM_REPORT):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_SALES_PER_ITEM_REPORT)
            self.close()
            return
        
        # Refresh the data
        self.show_sales_per_item_data()


    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_R_SALES_PER_ITEM_REPORT):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_SALES_PER_ITEM_REPORT)
            return
        
        # Refresh the data
        self.show_sales_per_item_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_R_SALES_PER_ITEM_REPORT):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_SALES_PER_ITEM_REPORT)
            return
        
        # Refresh the data
        self.show_sales_per_item_data()


    # Shows
    # ==============
    def show_sales_per_item_data(self):
        if not self.permission_manager.has_permission(PERM_R_SALES_PER_ITEM_REPORT):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_SALES_PER_ITEM_REPORT)
            return
        
        # Temporarily disable sorting
        self.sales_per_item_table.setSortingEnabled(False)
        
        # Get Dates
        start_date = datetime.strptime(self.ui.start_date_sales_per_item_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')
        end_date = datetime.strptime(self.ui.end_date_sales_per_item_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')

        category_id = None
        if self.ui.back_office_sales_radio_button.isChecked():
            category_id = BACKOFFICE_ID
        elif self.ui.cashier_sales_radio_button.isChecked():
            category_id = CASHIER_ID
        elif self.ui.all_sales_radio_button.isChecked():
            category_id = None


        sku = self.ui.sku_sales_per_item_input.text().strip().upper()

        # Get all reports
        sales_per_item_result = self.sales_per_item_report_service.get_sales_per_item_report(
            start_date = start_date.replace(hour=0, minute=0, second=0),
            end_date = end_date.replace(hour=23, minute=59, second=59),
            sku = sku,
            category_id = category_id
        )

        # Set sales per item table data
        self.set_sales_per_item_table_data(sales_per_item_result.data)


    # Setters
    # ==============
    def set_sales_per_item_table_data(self, data: list[SalesPerItemReportModel]):
        # Clear the table
        self.sales_per_item_table.setRowCount(0)
        total_sales = 0
        list_of_items_sold = {}
        for sales in data:
            current_row = self.sales_per_item_table.rowCount()
            self.sales_per_item_table.insertRow(current_row)

            created_at_dt = datetime.strptime(sales.created_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = created_at_dt.strftime('%d %b %y %H:%M:%S')

            table_items =  [ 
                QtWidgets.QTableWidgetItem(sales.transaction_id),
                QtWidgets.QTableWidgetItem(formatted_date),
                QtWidgets.QTableWidgetItem(sales.username),
                QtWidgets.QTableWidgetItem(str(sales.qty)),
                QtWidgets.QTableWidgetItem(str(sales.unit)),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(sales.price))),
                QtWidgets.QTableWidgetItem(str(sales.unit_value)),
                QtWidgets.QTableWidgetItem(str(sales.discount_pct)),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(sales.discount_rp_per_item))),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(sales.discount_rp))),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(sales.sub_total)))
            ]

            # Add Total Sales
            total_sales += sales.sub_total

            # Add List of Items Sold
            if sales.unit_value not in list_of_items_sold:
                list_of_items_sold[sales.unit] = {
                    'unit' : sales.unit,
                    'unit_value' : sales.unit_value,
                    'unit_sold' : sales.qty,
                }
            else:
                list_of_items_sold[sales.unit_value]['unit_sold'] += sales.qty


            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.sales_per_item_table.setItem(current_row, col, item)


        # Set total sales
        self.ui.total_transactions_input.setText(add_prefix(format_number(total_sales)))

        # Sorting in descending order
        sorted_dict_desc = dict(sorted(list_of_items_sold.items(), key=lambda item: item[1]['unit_value'], reverse=True))

        # Set list of items sold
        items_sold = [ f"{value['unit_sold']} {value['unit']}" for _, value in sorted_dict_desc.items() ]
        self.ui.total_items_sold_input.setText(' '.join(items_sold))

        self.sales_per_item_table.setSortingEnabled(True)

    
    # Event Listeners
    # ==============
    def on_handle_sku_enter(self):
        sku = self.ui.sku_sales_per_item_input.text().strip().upper()
        if not sku:
            return

        # Try to find exact SKU match
        result = self.sales_per_item_report_service.get_product_by_sku(sku)
        
        if result['success']:
            # Product found - fill the form
            self.handle_product_selected({'sku' : sku})

        else:
            # Product not found - show dialog with filter
            self.products_dialog.set_filter(sku)
            self.products_dialog.show()


    def handle_product_selected(self, product_data):
        # Clear Product Name Input
        self.ui.product_name_sales_per_item_input.clear()

        sku = product_data['sku']
        product_result = self.sales_per_item_report_service.get_product_by_sku(sku)
        if product_result['success']:
            # Set SKU Input
            self.ui.sku_sales_per_item_input.setText(sku)
            self.ui.product_name_sales_per_item_input.setText(product_result['data'].product_name)
