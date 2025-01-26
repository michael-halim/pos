from PyQt6 import QtWidgets, uic, QtGui, QtCore
from connect_db import DatabaseConnection


class AddProductWindow(QtWidgets.QWidget):
    # Add signal definition at class level
    product_added = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi("./ui/add_edit_product.ui", self)
        
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()


        # Connect the button to the function
        self.ui.submit_add_edit_product_button.clicked.connect(lambda: self.add_product())
        self.ui.cancel_add_edit_product_button.clicked.connect(lambda: self.close())

    
    def add_product(self):
       # Get the data from the input fields
        sku = self.ui.sku_input.text().strip()
        product_name = self.ui.product_name_input.text().strip()
        cost_price = self.ui.cost_price_input.text().replace('Rp.', '').strip()
        price = self.ui.price_input.text().replace('Rp.', '').strip()
        stock = self.ui.stock_input.text().strip()
        remarks = self.ui.remarks_input.toPlainText().strip()

        # Print the input for debugging
        print(sku, product_name, cost_price, price, stock, remarks)

        try:
            # Use parameterized query to prevent SQL injection
            sql = """
                INSERT INTO products (sku, product_name, cost_price, price, stock, remarks) 
                VALUES (?, ?, ?, ?, ?, ?)
            """

            self.cursor.execute(sql, (sku, product_name, cost_price, price, stock, remarks))
            
            # Commit changes if everything is successful
            self.db.commit()
            # Emit signal after successful addition
            self.product_added.emit()

        except Exception as e:
            # Rollback the transaction in case of error
            self.db.rollback()
            print(f"Transaction failed: {e}")

        # Close the dialog
        self.close()



class ProductsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi("./ui/products.ui", self)
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        
        # Init Dialog(s)
        self.add_product_dialog = AddProductWindow()
        self.products_table = self.ui.products_table

        self.show_data()
       

        # Connect the signal to refresh table
        self.add_product_dialog.product_added.connect(self.show_data)

        # Connect the button to the function
        self.ui.add_product_button.clicked.connect(lambda: self.add_product_dialog.show())
    
    def show_data(self):
        self.products_table = self.ui.products_table
        self.products_table.setRowCount(0)

        # Get data from the database
        sql = "SELECT sku, cost_price, price, stock, remarks FROM products LIMIT 100"
        self.cursor.execute(sql)
        products_result = self.cursor.fetchall()

        # Display the data in the table
        self.ui.products_table.setRowCount(len(products_result))

        for row_num, product in enumerate(products_result):
            action_edit = QtGui.QAction("Edit", self)
            action_delete = QtGui.QAction("Delete", self)

            # Create QMenu
            menu = QtWidgets.QMenu(self)
            # Add actions to each row
            menu.addActions([action_edit, action_delete])

            option_btn = QtWidgets.QPushButton(self)
            option_btn.setText("Option")
            option_btn.setMenu(menu)
            
            row_data = [p for p in product] + [option_btn]

            for col_num, data in enumerate(row_data):
                if col_num == 5:
                    # Set the cell widget for actions for delete and edit
                    self.ui.products_table.setCellWidget(row_num, col_num, data)
                else:
                    self.ui.products_table.setItem(row_num, col_num, QtWidgets.QTableWidgetItem(str(data)))
