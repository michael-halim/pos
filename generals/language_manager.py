from PyQt6 import QtWidgets, QtCore

from generals.translate import EN_TRANSLATIONS, ID_TRANSLATIONS


class LanguageManager:
    _instance = None
    always_caps = ['sku', 'bo', 'so #']

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
 
        # Skip translating values in input fields
        if isinstance(widget, (QtWidgets.QDateEdit, QtWidgets.QSpinBox, QtWidgets.QLineEdit, QtWidgets.QPlainTextEdit, QtWidgets.QTextEdit)):
            return 
        
        # Translate text in a widget (label, button, etc.)
        if hasattr(widget, 'text') and callable(getattr(widget, 'text')):
            current_text = widget.text()
            if current_text:
                translated_text = self.translate(current_text.lower())
                if translated_text.lower().strip().replace(' :','') in self.always_caps:
                    widget.setText(translated_text.upper())
                else:
                    widget.setText(translated_text.title())
        

        # Special case for window titles
        if hasattr(widget, 'windowTitle') and callable(getattr(widget, 'windowTitle')):
            title = widget.windowTitle()
            if title:
                translated_title = self.translate(title)
                if translated_title.lower().strip() == 'pos':
                    widget.setWindowTitle(translated_title.upper())
                else:
                    widget.setWindowTitle(translated_title.title())
        
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
            if translated_header in self.always_caps:
                item.setText(translated_header.upper())
            else:
                item.setText(translated_header.title())


# Helper function for easy translation
def tr(text):
    """Helper function for translation"""
    return LanguageManager().translate(text)
    