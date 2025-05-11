from PyQt6 import QtWidgets, uic, QtCore, QtGui

from dialogs.roles_dialog.models.roles_dialog_models import RolesModel, PermissionsModel
from dialogs.roles_dialog.services.roles_dialog_services import RolesDialogService

from generals.fonts import POSFonts
from generals.build import resource_path
from generals.widget import create_checkbox_item
from generals.message_box import POSMessageBox
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    PERM_R_ROLES
) 
from generals.messages import ERR, ERR_PERM_R_ROLES, PERM_DENIED
from generals.permission_manager import PermissionManager
from dialogs.roles_dialog.translations import ROLES_DIALOG_TRANSLATIONS
from generals.language_manager import LanguageManager


class RolesDialogWindow(QtWidgets.QWidget):
    role_selected = QtCore.pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_ROLES):
            return

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/roles_dialog.ui'), self)

        # Init Services
        self.roles_dialog_service = RolesDialogService()

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(ROLES_DIALOG_TRANSLATIONS)

        # Init Table
        self.roles_table = self.ui.roles_table
        self.permissions_table = self.ui.permissions_table
        
        # Init Button
        self.ui.add_roles_dialog_button.clicked.connect(self.send_role_data)
        self.ui.close_roles_dialog_button.clicked.connect(lambda: self.close())
        
        # # Connect search input to filter function
        self.ui.filter_roles_input.textChanged.connect(self.show_roles_data)
        self.ui.filter_permissions_input.textChanged.connect(self.show_permissions_data)

        # Set selection behavior to select entire rows
        self.roles_table.setSelectionBehavior(SELECT_ROWS)
        self.roles_table.setSelectionMode(SINGLE_SELECTION)
        self.permissions_table.setSelectionBehavior(SELECT_ROWS)
        self.permissions_table.setSelectionMode(SINGLE_SELECTION)

        self.roles_table.setEditTriggers(NO_EDIT_TRIGGERS)
        self.permissions_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties
        self.roles_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.roles_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        self.permissions_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.permissions_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        # Connect table selection
        self.roles_table.itemSelectionChanged.connect(self.on_role_selected)
        
        self.show_roles_data()


    # Overrides
    # ===============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_R_ROLES):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_R_ROLES)
            self.close()
            return

        # Set window title
        if self.permission_manager.get_username().lower() not in self.windowTitle().lower():
            self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username())

        # Translate Widget Text
        self.language_manager.translate_widget_text(self)

        self.roles_headers = ['ID', 'Role Name', 'Description']
        self.permissions_headers = ['#', 'Permissions']
        if self.language_manager.get_current_language() == 'id':
            self.roles_headers = ['ID', 'Nama Jabatan', 'Deskripsi']
            self.permissions_headers = ['#', 'Hak Akses']

        self.language_manager.translate_table_headers(self.roles_table, self.roles_headers)
        self.language_manager.translate_table_headers(self.permissions_table, self.permissions_headers)

        # Refresh the data
        self.show_roles_data()


    def show(self):
        """Override show to ensure data is refreshed"""
        super().show()
        if not self.permission_manager.has_permission(PERM_R_ROLES):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_R_ROLES)
            return

        # Refresh the data
        self.show_roles_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_R_ROLES):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_R_ROLES)
            return

        # Refresh the data
        self.show_roles_data()


    # Setters
    # ===============
    def set_roles_table_data(self, data: list[RolesModel]):
        # Clear the table
        self.roles_table.setRowCount(0)

        for role in data:
            current_row = self.roles_table.rowCount()
            self.roles_table.insertRow(current_row)

            table_items =  [ 
                QtWidgets.QTableWidgetItem(str(role.role_id)),
                QtWidgets.QTableWidgetItem(role.role_name),
                QtWidgets.QTableWidgetItem(role.role_description),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.roles_table.setItem(current_row, col, item)

        self.roles_table.setSortingEnabled(True)


    def set_permissions_table_data(self, data: list[PermissionsModel], allowed_permissions: set[str]):
        # Clear the table
        self.permissions_table.setRowCount(0)

        for permission in data:
            current_row = self.permissions_table.rowCount()
            self.permissions_table.insertRow(current_row)

            permission_id = str(permission.permission_id)

            # Create checkbox item
            checkbox_item = create_checkbox_item(permission_id, is_editable=False, size=22)

            # Checked if permission is allowed
            is_checked = QtCore.Qt.CheckState.Unchecked
            checkbox_item.setBackground(QtGui.QColor(0xF8, 0xD7, 0xDA))
            if permission_id in allowed_permissions:
                is_checked = QtCore.Qt.CheckState.Checked
                checkbox_item.setBackground(QtGui.QColor(0xD1, 0xE7, 0xDD))

            checkbox_item.setCheckState(is_checked)
            
            self.permissions_table.setItem(current_row, 0, checkbox_item)
            
            table_items =  [
                QtWidgets.QTableWidgetItem(permission.permission_name),
            ]

            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                item.setBackground(QtGui.QColor(0xF8, 0xD7, 0xDA))
                if is_checked == QtCore.Qt.CheckState.Checked:
                    item.setBackground(QtGui.QColor(0xD1, 0xE7, 0xDD))

                self.permissions_table.setItem(current_row, col + 1, item)

        self.permissions_table.setSortingEnabled(True)


    # Signal Handlers
    # ===============
    def send_role_data(self):
        selected_rows = self.roles_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            
            # Create dictionary with product details
            role_data = {
                'role_id': self.roles_table.item(row, 0).text(),
            }
            
            # Emit signal with product data
            self.role_selected.emit(role_data)
            self.close()


    def set_filter(self, search_text: str):
        """Pre-fill the search filter"""
        self.ui.filter_roles_input.setText(search_text)

        # Optionally trigger the filter
        self.show_roles_data()


    # Shows
    # ===============
    def show_roles_data(self):

        self.roles_table.setSortingEnabled(False)

        search_text = self.ui.filter_roles_input.text().strip()
        search_text = search_text.lower() if search_text else None

        roles_result = self.roles_dialog_service.get_roles(search_text)

        if not roles_result.success:
            POSMessageBox.error(self, title=ERR, message=roles_result.message)
            return

        self.set_roles_table_data(roles_result.data)


    def show_permissions_data(self):
        search_text = self.ui.filter_permissions_input.text().strip().lower()
        
        # Show all rows if search text is empty
        if not search_text:
            for row in range(self.permissions_table.rowCount()):
                self.permissions_table.setRowHidden(row, False)
            return
        
        # Iterate through all rows
        for row in range(self.permissions_table.rowCount()):
            match_found = False
            
            # Search through all columns in the row
            for col in range(self.permissions_table.columnCount()):
                item = self.permissions_table.item(row, col)
                if item and search_text in item.text().lower():
                    match_found = True
                    break
            
            # Hide/show row based on whether match was found
            self.permissions_table.setRowHidden(row, not match_found)


    # Event Listeners
    # ===============
    def on_role_selected(self):
        selected_rows = self.roles_table.selectedItems()
        if selected_rows:
            self.current_selected_role = selected_rows[0].row()

            # Get Role Id
            role_id = self.roles_table.item(self.current_selected_role, 0).text()
            
            # Get All Permissions
            permissions = self.roles_dialog_service.get_permissions()

            # Get Allowed Permissions
            allowed_permissions = self.roles_dialog_service.get_permissions_by_role_id(role_id)
        
            self.set_permissions_table_data(permissions.data, allowed_permissions.data)

    
    def set_filter(self, search_text: str):
        """Pre-fill the search filter"""
        self.ui.filter_roles_input.setText(search_text)
        # Optionally trigger the filter
        self.filter_roles()


    def filter_roles(self):
        search_text = self.ui.filter_roles_input.text().lower()
        for row in range(self.roles_table.rowCount()):
            match_found = False
            for col in range(self.roles_table.columnCount()):
                item = self.roles_table.item(row, col)
                if item and search_text in item.text().lower():
                    match_found = True
                    break
            self.roles_table.setRowHidden(row, not match_found)



    # Event Filters
    # ===============
    def keyPressEvent(self, event):
        # If no row is selected, select the first row if available
        if event.key() == QtCore.Qt.Key.Key_Down:
            if self.roles_table.rowCount() > 0 and not self.roles_table.selectedItems():
                self.roles_table.selectRow(0)
                self.roles_table.setFocus()
                event.accept()
                return
            

        # Check for Enter key
        if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            # Don't handle Enter if we're in a text field
            if not isinstance(QtWidgets.QApplication.focusWidget(), QtWidgets.QLineEdit):
                # If a row is selected or there are rows, send the data
                if self.roles_table.rowCount() > 0:
                    if not self.roles_table.selectedItems():
                        self.roles_table.selectRow(0)
                    self.send_role_data()
                    return
        
        
        # Let the parent class handle other keys
        super().keyPressEvent(event)