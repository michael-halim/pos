from .services.import_products_dialog_services import ImportProductsDialogService
from .models.import_products_dialog_models import ImportProductsDialogModel
from generals.build import resource_path
from PyQt6 import QtWidgets, uic
import openpyxl


class ImportProductsDialogWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.service = ImportProductsDialogService()

        self.ui = uic.loadUi(resource_path('ui/import_products.ui'), self)

        self.ui.close_import_products_button.clicked.connect(lambda: self.close())

        self.ui.select_file_import_products_button.clicked.connect(self.select_file)
        self.ui.submit_import_products_button.clicked.connect(self.submit_import_products)


    def select_file(self):
        # Open a folder dialog and get the selected file path
        folder_path = QtWidgets.QFileDialog.getOpenFileName(self, caption="Open Folder",
                                                            filter="*.xlsx")

        # Check if a file path was selected
        if folder_path[0]:
            # Clear any existing text in the target_file_path widget
            self.ui.file_name_import_products_input.clear()
            self.ui.file_name_import_products_input.setText(folder_path[0])


    def submit_import_products(self):
        file_path = self.ui.file_name_import_products_input.text()
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active

        for co, row in enumerate(sheet.iter_rows()):
            if co == 0:
                continue

            sku, product_name, barcode, unit, cost_price, price, stock, remarks = \
            row[0].value, row[1].value, row[2].value, row[3].value, row[4].value, row[5].value, row[6].value, row[7].value

            if sku is None or product_name is None or unit is None or price is None or stock is None:
                self.ui.error_import_products_input.setText(f'Error Import For Row {co}, SKU: {sku}, Product Name: {product_name}, Unit: {unit}, Price: {price}, Stock: {stock}')
                self.ui.error_import_products_input.setStyleSheet('color: red;')
                return
            
            sku, product_name, barcode, unit, cost_price, price, stock, remarks = \
            str(sku), str(product_name), str(barcode), str(unit), str(cost_price), str(price), str(stock), str(remarks)


            if sku.strip() == '' or product_name.strip() == '' or unit.strip() == '' or price.strip() == '' or stock.strip() == '':
                self.ui.error_import_products_input.setText(f'Error Import For Row {co}, SKU: {sku}, Product Name: {product_name}, Unit: {unit}, Price: {price}, Stock: {stock}')
                self.ui.error_import_products_input.setStyleSheet('color: red;')
                return