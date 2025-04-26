from PyQt6 import QtWidgets, QtCore

from generals.translate import EN_TRANSLATIONS, ID_TRANSLATIONS


class LanguageManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize with default language
            cls._instance._current_language = 'en'  # Default to English
            cls._instance._translations = {
                'en': {},
                'id': {}
            }
            cls._instance._load_default_translations()
        return cls._instance
    

    def _load_default_translations(self):
        """Load default translations"""
        self._translations['en'] = EN_TRANSLATIONS
        self._translations['id'] = ID_TRANSLATIONS
        
    
    def translate(self, text):
        """Translate text to current language"""
        return self._translations.get(self._current_language, {}).get(text.lower(), text)
    

    def get_current_language(self):
        """Get current language code"""
        return self._current_language
    

    def set_language(self, language_code):
        """Set current language (en or id)"""
        if language_code in ['en', 'id']:
            self._current_language = language_code
            return True
        return False
        

    def add_translations(self, module_translations):
        """Add module-specific translations temporarily
        
        Args:
            module_translations (dict): Dictionary with 'en' and 'id' keys, each containing
                                        a dictionary of translations
        """
        if not isinstance(module_translations, dict):
            return
            
        # Add English translations
        if 'en' in module_translations and isinstance(module_translations['en'], dict):
            for key, value in module_translations['en'].items():
                self._translations['en'][key.lower()] = value
                
        # Add Indonesian translations
        if 'id' in module_translations and isinstance(module_translations['id'], dict):
            for key, value in module_translations['id'].items():
                self._translations['id'][key.lower()] = value
    

    def translate_widget_text(self, widget):
        """Translate text in a widget (label, button, etc.)"""
 
        if isinstance(widget, QtWidgets.QDateEdit):
            return 
        
        
        if hasattr(widget, 'text') and callable(getattr(widget, 'text')):
            current_text = widget.text()
            if current_text:
                print('current_text: ', current_text)
                translated_text = self.translate(current_text.lower())
                print('translated_text: ', translated_text)
                widget.setText(translated_text.title())
        

        # Special case for window titles
        if hasattr(widget, 'windowTitle') and callable(getattr(widget, 'windowTitle')):
            title = widget.windowTitle()
            if title:
                translated_title = self.translate(title)
                widget.setWindowTitle(translated_title)
        
        # Handle table widgets and their headers
        if isinstance(widget, QtWidgets.QTableWidget):
            # Translate horizontal headers if they exist
            if widget.horizontalHeader():
                for col in range(widget.columnCount()):
                    header_item = widget.horizontalHeaderItem(col)
                    if header_item and header_item.text():
                        header_text = header_item.text()
                        translated_header = self.translate(header_text.lower())
                        header_item.setText(translated_header.title())
            
            # Translate vertical headers if they exist
            if widget.verticalHeader():
                for row in range(widget.rowCount()):
                    header_item = widget.verticalHeaderItem(row)
                    if header_item and header_item.text():
                        header_text = header_item.text()
                        translated_header = self.translate(header_text.lower())
                        header_item.setText(translated_header.title())
                        
        # Handle table views (QTableView)
        if isinstance(widget, QtWidgets.QTableView) and widget.model():
            model = widget.model()
            # Translate horizontal headers
            for col in range(model.columnCount()):
                header_data = model.headerData(col, QtCore.Qt.Orientation.Horizontal)
                if header_data and isinstance(header_data, str):
                    translated_header = self.translate(header_data.lower())
                    model.setHeaderData(col, QtCore.Qt.Orientation.Horizontal, translated_header.title())
            
            # Translate vertical headers
            for row in range(model.rowCount()):
                header_data = model.headerData(row, QtCore.Qt.Orientation.Vertical)
                if header_data and isinstance(header_data, str):
                    translated_header = self.translate(header_data.lower())
                    model.setHeaderData(row, QtCore.Qt.Orientation.Vertical, translated_header.title())
                
        # Process all child widgets
        for child in widget.findChildren(QtWidgets.QWidget):
            self.translate_widget_text(child)


    def translate_table_headers(self, table_widget, headers):
        """Translate and update table headers
        
        Args:
            table_widget (QTableWidget): The table widget to update
            headers (list): List of header texts in original language
        """
        if not isinstance(table_widget, QtWidgets.QTableWidget):
            return
        
        # Ensure column count matches headers
        if table_widget.columnCount() != len(headers):
            table_widget.setColumnCount(len(headers))
        
        # Update translated headers
        for col, header in enumerate(headers):
            translated_header = self.translate(header.lower())
            
            # Get existing header item or create a new one
            item = table_widget.horizontalHeaderItem(col)
            if not item:
                item = QtWidgets.QTableWidgetItem()
                table_widget.setHorizontalHeaderItem(col, item)
            
            # Set translated text
            item.setText(translated_header.title())


# Helper function for easy translation
def tr(text):
    """Helper function for translation"""
    return LanguageManager().translate(text)
    