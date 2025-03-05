from PyQt6 import QtWidgets, uic, QtGui
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta

from helper import format_number, add_prefix, remove_non_digit
from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS
from generals.build import resource_path

from stock_card_list.services.stock_card_list_services import StockCardListService
from stock_card_list.models.stock_card_list_models import ProductStockCardListModel, StockCardListModel


class StockCardListWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/stock_card_list.ui'), self)

        # Init Services
        self.stock_card_list_service = StockCardListService()

        # Init Tables
        self.products_table = self.ui.products_table
        self.stock_card_table = self.ui.stock_card_table

        # Connect Find Stock Card Button
        self.ui.find_stock_card_button.clicked.connect(self.show_stock_card_data)


        # Connect filter products input
        self.ui.filter_products_stock_card_input.textChanged.connect(self.show_products_data)

        # Connect table selection
        self.products_table.itemSelectionChanged.connect(self.on_product_selected)

        # Set date input
        self.ui.start_date_stock_card_input.setDate(datetime.now() - timedelta(days=1))
        self.ui.end_date_stock_card_input.setDate(datetime.now())

        self.ui.start_date_stock_card_input.setDisplayFormat("dd/MM/yyyy")
        self.ui.end_date_stock_card_input.setDisplayFormat("dd/MM/yyyy")


        # Set selection behavior to select entire rows
        self.products_table.setSelectionBehavior(SELECT_ROWS)
        self.products_table.setSelectionMode(SINGLE_SELECTION)
        self.stock_card_table.setSelectionBehavior(SELECT_ROWS)
        self.stock_card_table.setSelectionMode(SINGLE_SELECTION)

        # Set wholesale purchasing table to be read only
        self.products_table.setEditTriggers(NO_EDIT_TRIGGERS)
        self.stock_card_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.products_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.products_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.stock_card_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.stock_card_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        # Show data for both tables
        self.show_products_data()


    # Overrides
    # ===============
    def showEvent(self, event):
        super().showEvent(event)


    def show(self):
        super().show()
    
   
    def showMaximized(self):
        super().showMaximized()


    # Shows
    # ===============
    def show_products_data(self):

        self.products_table.setSortingEnabled(False)

        search_text = self.ui.filter_products_stock_card_input.text().strip()
        search_text = search_text.lower() if search_text else None

        products_result = self.stock_card_list_service.get_products(search_text)

        self.set_products_table_data(products_result.data)

        self.products_table.setSortingEnabled(True)


    def show_stock_card_data(self):
        selected_product = self.products_table.selectedItems()
        if not selected_product:
            return
        
        row = selected_product[0].row()
        sku = self.products_table.item(row, 0).text()

        self.stock_card_table.setSortingEnabled(False)

        start_date = datetime.strptime(self.ui.start_date_stock_card_input.date().toString('dd/MM/yyyy'), '%d/%m/%Y')
        end_date = datetime.strptime(self.ui.end_date_stock_card_input.date().toString('dd/MM/yyyy'), '%d/%m/%Y')

        stock_card_result = self.stock_card_list_service.get_stock_card(sku, start_date, end_date)

        self.set_stock_card_table_data(stock_card_result.data)

        self.stock_card_table.setSortingEnabled(True)

    
    # Setters
    # ===============
    def set_products_table_data(self, data: list[ProductStockCardListModel]):
        # Clear the table
        self.products_table.setRowCount(0)

        for product in data:
            current_row = self.products_table.rowCount()
            self.products_table.insertRow(current_row)


            # Change stock color if negative
            current_stock = QtWidgets.QTableWidgetItem(str(product.current_stock))
            if product.current_stock < 0:
                current_stock = QtWidgets.QTableWidgetItem(f'-{format_number(str(product.current_stock))}')
                current_stock.setForeground(QtGui.QColor(255, 0, 0))


            table_items =  [ 
               QtWidgets.QTableWidgetItem(product.sku),
               QtWidgets.QTableWidgetItem(product.product_name),
               current_stock,
               QtWidgets.QTableWidgetItem(product.unit),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.products_table.setItem(current_row, col, item)    


    def set_stock_card_table_data(self, data: list[StockCardListModel]):
        # Clear the table
        self.stock_card_table.setRowCount(0)

        for stock_card in data:
            current_row = self.stock_card_table.rowCount()
            self.stock_card_table.insertRow(current_row)

            # Set stock in and align center
            stock_in = QtWidgets.QTableWidgetItem('-')
            
            if stock_card.stock_in is not None:
                stock_in = QtWidgets.QTableWidgetItem(format_number(str(stock_card.stock_in)))
                stock_in.setForeground(QtGui.QColor(0, 0, 255))

            stock_in.setTextAlignment(Qt.AlignmentFlag.AlignCenter)


            # Set stock out and align center
            stock_out = QtWidgets.QTableWidgetItem('-')
            if stock_card.stock_out is not None:
                stock_out = QtWidgets.QTableWidgetItem(format_number(str(stock_card.stock_out)))
                stock_out.setForeground(QtGui.QColor(0, 255, 0))

            stock_out.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Change running balance color if negative and align center
            running_balance = QtWidgets.QTableWidgetItem(str(stock_card.running_balance))
            if stock_card.running_balance < 0:
                running_balance = QtWidgets.QTableWidgetItem(f'-{format_number(str(stock_card.running_balance))}')
                running_balance.setForeground(QtGui.QColor(255, 0, 0))

            running_balance.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Set date
            tmp_date = datetime.strptime(stock_card.date, '%Y-%m-%d')
            formatted_date = tmp_date.strftime('%d %b %y')
            
            # Set time
            tmp_time = datetime.strptime(stock_card.time, '%H:%M:%S')
            formatted_time = tmp_time.strftime('%H:%M')

            table_items =  [ 
               QtWidgets.QTableWidgetItem(formatted_date),
               QtWidgets.QTableWidgetItem(formatted_time),
               QtWidgets.QTableWidgetItem(stock_card.transaction_id),
               stock_in,
               stock_out,
               running_balance,
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.stock_card_table.setItem(current_row, col, item)    


    # Event Listeners
    # ===============
    def on_product_selected(self):
        selected_rows = self.products_table.selectedItems()
        if selected_rows:
            # Get the first selected row
            row = selected_rows[0].row()
            selected_sku = self.products_table.item(row, 0).text()
            
            start_date = datetime.strptime(self.ui.start_date_stock_card_input.date().toString('dd/MM/yyyy'), '%d/%m/%Y')   
            end_date = datetime.strptime(self.ui.end_date_stock_card_input.date().toString('dd/MM/yyyy'), '%d/%m/%Y')

            stock_card_results = self.stock_card_list_service.get_stock_card(selected_sku, start_date, end_date)
            if stock_card_results.success:
                self.set_stock_card_table_data(stock_card_results.data)

            else:
                POSMessageBox.error(self, title="Error", message=stock_card_results.message)
