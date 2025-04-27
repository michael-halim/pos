from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import pyqtSignal

from dialogs.import_products_dialog.services.import_products_dialog_services import ImportProductsDialogService

from generals.build import resource_path
from generals.message_box import POSMessageBox
from dialogs.import_products_dialog.translations import IMPORT_PRODUCTS_DIALOG_TRANSLATIONS
from generals.language_manager import LanguageManager


class ImportProductsDialogWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.import_products_service = ImportProductsDialogService()

        self.ui = uic.loadUi(resource_path('ui/import_products.ui'), self)

        self.ui.close_import_products_button.clicked.connect(lambda: self.close())

        self.ui.select_file_import_products_button.clicked.connect(self.select_file)
        self.ui.submit_import_products_button.clicked.connect(self.submit_import_products)
        

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(IMPORT_PRODUCTS_DIALOG_TRANSLATIONS)

        # Translate Widget Text
        self.language_manager.translate_widget_text(self)
        

    def select_file(self):
        # Open a folder dialog and get the selected file path
        folder_path = QtWidgets.QFileDialog.getOpenFileName(self, caption="Open Folder",filter="*.xlsx")

        # Check if a file path was selected
        if folder_path[0]:
            # Clear any existing text in the target_file_path widget
            self.ui.file_name_import_products_input.clear()
            self.ui.file_name_import_products_input.setText(folder_path[0])
            # Clear any previous error messages
            self.ui.log_import_products_input.clear()


    def submit_import_products(self):
        file_path = self.ui.file_name_import_products_input.text()
        
        if not file_path:
            self.ui.log_import_products_input.setText("Please select a file first")
            self.ui.log_import_products_input.setStyleSheet('color: red;')
            return
            
        # Disable the submit button while processing
        self.ui.submit_import_products_button.setEnabled(False)
        self.ui.log_import_products_input.setText("Processing file, please wait...")
        self.ui.log_import_products_input.setStyleSheet('color: blue;')
        
        # Start the import process in a background thread
        self.import_products_service.import_products(
            file_path, 
            self.on_complete, 
            self.on_error, 
            self.on_progress
        )


    def on_import_complete(self, result):
        """Handle successful import completion"""
        if result.success:
            POSMessageBox.info(self, title="Success", message=result.message)
        else:
            POSMessageBox.error(self, title="Error", message=result.message)
        

    def on_complete(self, result):
        """Handle successful import completion"""

        # Re-enable the submit button
        self.ui.submit_import_products_button.setEnabled(True)
        
        if not result:
            self.ui.log_import_products_input.setText("No data was processed")
            self.ui.log_import_products_input.setStyleSheet('color: red;')
            return
            
        # Check if there were any errors
        if result['errors']:
            # Show the first error
            self.ui.log_import_products_input.setText(result['errors'][0]['message'])
            self.ui.log_import_products_input.setStyleSheet('color: red;')
        else:
            # Show success message
            self.ui.log_import_products_input.setText(f"Successfully processed {result['valid_count']} products")
            self.ui.log_import_products_input.setStyleSheet('color: green;')
            
            self.import_products_service.import_products_to_database(result['valid_products'], self.on_import_complete)
            
            
    def on_error(self, error):
        """Handle import error"""
        # Re-enable the submit button
        self.ui.submit_import_products_button.setEnabled(True)
        
        # Show error message
        self.ui.log_import_products_input.setText(f"Error: {error}")
        self.ui.log_import_products_input.setStyleSheet('color: red;')


    def on_progress(self, progress):
        """Handle progress updates"""
        print('on_progress ', progress)
