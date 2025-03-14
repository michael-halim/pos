from PyQt6 import QtWidgets, uic, QtGui
from datetime import datetime

from dialogs.roles_dialog.roles_dialog import RolesDialogWindow
from dialogs.change_password_dialog.change_password_dialog import ChangePasswordDialogWindow

from users.services.users_services import UsersService
from users.models.users_models import UsersTableItemModel, UsersFormModel

from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.build import resource_path
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    PERM_R_USERS, PERM_C_USERS, PERM_U_USERS, PERM_D_USERS,
) 
from generals.messages import (
    ERR, OK, ERR_PERM_R_USERS, ERR_PERM_C_USERS, ERR_PERM_U_USERS, ERR_PERM_D_USERS,
    PERM_DENIED
)
from generals.permission_manager import PermissionManager

class UsersWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_USERS):
            return

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/users.ui'), self)

        # Setup permissions
        self.setup_permissions()

        # Init Dialog
        self.roles_dialog = RolesDialogWindow()
        self.change_password_dialog = ChangePasswordDialogWindow()

        # Init Services
        self.users_service = UsersService()

        self.users_table = self.ui.users_table

        # Connect search input to filter function
        self.ui.filter_users_input.textChanged.connect(self.show_users_data)
        self.ui.toggle_active_users_button.clicked.connect(self.toggle_active_users)
        self.ui.clear_users_button.clicked.connect(self.clear_users_form_data)
        self.ui.create_new_users_button.clicked.connect(self.create_new_users)
        self.ui.edit_users_button.clicked.connect(self.edit_users)
        self.ui.delete_users_button.clicked.connect(self.delete_users)
        self.ui.submit_users_button.clicked.connect(self.submit_users)
        self.ui.change_password_users_button.clicked.connect(lambda: self.change_password_dialog.show())
        self.ui.close_users_button.clicked.connect(lambda: self.close())

        # Listen selected row in tables
        self.users_table.itemSelectionChanged.connect(self.on_user_selected)

        # Connect the role_selected signal to handle_role_selected method
        self.roles_dialog.role_selected.connect(self.handle_role_selected)

        # Connect to handle change password dialog
        self.change_password_dialog.password_changed.connect(self.handle_change_password)

        # Connect the find_role_users_button to the roles_dialog
        self.ui.find_role_users_button.clicked.connect(lambda: self.roles_dialog.show())

        # Connect on enter key press on roles input
        self.ui.role_id_users_input.returnPressed.connect(self.on_handle_role_enter)

        # Set selection behavior to select entire rows
        self.users_table.setSelectionBehavior(SELECT_ROWS)
        self.users_table.setSelectionMode(SINGLE_SELECTION)

        # Set edit triggers to no edit
        self.users_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties
        self.users_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.users_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        self.show_users_data()


    # Overrides
    # ===============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_R_USERS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_USERS)
            self.close()
            return
        # Refresh the data
        self.show_users_data()


    def show(self):
        """Override show to ensure data is refreshed"""
        super().show()
        if not self.permission_manager.has_permission(PERM_R_USERS):
            return
        # Refresh the data
        self.show_users_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_R_USERS):
            return
        # Refresh the data
        self.show_users_data()


    def toggle_active_users(self):
        if not self.permission_manager.has_permission(PERM_U_USERS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_U_USERS)
            return

        selected_row = self.users_table.selectedItems()
        if not selected_row:
            POSMessageBox.error(self, title=ERR, message="Please select a user to toggle status")
            return

        row = selected_row[0].row()
        user_id = self.users_table.item(row, 0).text()
        is_active = self.users_table.item(row, 3).text().strip() == 'Active'

        user_result = self.users_service.set_user_status(user_id, not is_active)
        if user_result.success:
            POSMessageBox.info(self, title=OK, message=user_result.message)
            self.show_users_data()

        else:
            POSMessageBox.error(self, title=ERR, message=user_result.message)


    def create_new_users(self):
        if not self.permission_manager.has_permission(PERM_C_USERS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_C_USERS)
            return

        self.clear_users_form_data()
        self.set_enabled_users_form_group(True)
        self.ui.change_password_users_button.setEnabled(False)
        self.ui.user_id_users_input.setEnabled(False)
        self.ui.user_id_users_input.setFocus()


    def edit_users(self):
        if not self.permission_manager.has_permission(PERM_U_USERS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_U_USERS)
            return

        # Get the selected row
        selected_user = self.ui.users_table.selectedItems()

        if selected_user:
            self.users_table.setSortingEnabled(False)

            row = selected_user[0].row()
            user_id = self.ui.users_table.item(row, 0).text()
            user_result = self.users_service.get_user_by_id(user_id)

            if user_result.success and user_result.data:
                # Set the form data
                self.set_users_form_data(user_result.data)
                self.set_enabled_users_form_group(True)
                
                self.ui.user_id_users_input.setEnabled(False)
                self.ui.username_users_input.setEnabled(False)
                self.ui.password_users_input.setEnabled(False)
                self.ui.change_password_users_button.setEnabled(True)

                self.ui.role_id_users_input.setFocus()

                # Set the submit button text and connect to update function
                self.ui.submit_users_button.setText('Update')
                self.ui.submit_users_button.clicked.disconnect()
                self.ui.submit_users_button.clicked.connect(self.update_users)

                self.users_table.setSortingEnabled(True)

        else:
            POSMessageBox.error(self, title=ERR, message="Please select a user to edit")
    

    def update_users(self):
        if not self.permission_manager.has_permission(PERM_U_USERS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_U_USERS)
            return

        self.users_table.setSortingEnabled(False)

        user_data = self.get_users_form_data()
        user_result = self.users_service.update_user(user_data)
        if user_result.success:
            POSMessageBox.info(self, title=OK, message=user_result.message)
            
            self.clear_users_form_data()
            self.show_users_data()
            self.set_enabled_users_form_group(False)

            # Set the submit button text and connect to submit function
            self.ui.submit_users_button.setText('Submit')
            self.ui.submit_users_button.clicked.disconnect()
            self.ui.submit_users_button.clicked.connect(self.submit_users)

        else:
            POSMessageBox.error(self, title=ERR, message=user_result.message)

        self.users_table.setSortingEnabled(True)


    def delete_users(self):
        if not self.permission_manager.has_permission(PERM_D_USERS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_D_USERS)
            return

        selected_row = self.users_table.selectedItems()
        if not selected_row:
            POSMessageBox.error(self, title=ERR, message="Please select a user to delete")
            return
        
        confirm = POSMessageBox.confirm(
                        self, title='Confirm Deletion', 
                        message='Are you sure you want to delete this user ?')

        if confirm:
            row = selected_row[0].row()
            user_id = self.users_table.item(row, 0).text()

            result = self.users_service.delete_user(user_id)
            if result.success:
                POSMessageBox.info(self, title=OK, message=result.message)

                self.set_enabled_users_form_group(False)
                self.clear_users_form_data()
                self.show_users_data()

            else:
                POSMessageBox.error(self, title=ERR, message=result.message)


    def submit_users(self):
        if not self.permission_manager.has_permission(PERM_C_USERS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_C_USERS)
            return

        # Disable Sorting to prevent data from being sorted
        self.users_table.setSortingEnabled(False)

        user_data = self.get_users_form_data()
        user_result = self.users_service.submit_user(user_data)
        if user_result.success:
            POSMessageBox.info(self, title=OK, message=user_result.message)
            self.clear_users_form_data()
            self.set_enabled_users_form_group(False)
            self.show_users_data()

        else:
            POSMessageBox.error(self, title=ERR, message=user_result.message)

        # Re-enable Sorting
        self.users_table.setSortingEnabled(True)


    # Setters
    # ===============
    def set_users_form_data(self, data: UsersFormModel):
        self.ui.user_id_users_input.setText(str(data.user_id))
        self.ui.username_users_input.setText(str(data.username))
        self.ui.role_id_users_input.setText(str(data.role_id))
        self.ui.role_name_users_input.setText(str(data.role_name))


    def set_users_table_data(self, data: list[UsersTableItemModel]):
         # Clear the table
        self.users_table.setRowCount(0)

        for user in data:
            current_row = self.users_table.rowCount()
            self.users_table.insertRow(current_row)

            created_at_user = datetime.strptime(user.created_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = created_at_user.strftime('%d %b %y %H:%M')

            is_active = QtWidgets.QTableWidgetItem(user.is_active)
            is_active.setText('Inactive')
            is_active.setBackground(QtGui.QColor(0xF8, 0xD7, 0xDA))
            if user.is_active:
                is_active.setText('Active')
                is_active.setBackground(QtGui.QColor(0xD1, 0xE7, 0xDD))

            table_items = [ 
                QtWidgets.QTableWidgetItem(str(user.user_id)),
                QtWidgets.QTableWidgetItem(user.username),
                QtWidgets.QTableWidgetItem(user.role_name),
                is_active,
                QtWidgets.QTableWidgetItem(formatted_date),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.users_table.setItem(current_row, col, item)

        self.users_table.setSortingEnabled(True)

    
    def set_enabled_users_form_group(self, is_enabled: bool):
        self.ui.user_id_users_input.setEnabled(is_enabled)
        self.ui.username_users_input.setEnabled(is_enabled)
        self.ui.password_users_input.setEnabled(is_enabled)
        self.ui.role_id_users_input.setEnabled(is_enabled)
        self.ui.find_role_users_button.setEnabled(is_enabled)
        self.ui.clear_users_button.setEnabled(is_enabled)
        self.ui.submit_users_button.setEnabled(is_enabled)
        self.ui.change_password_users_button.setEnabled(is_enabled)


    # Getters
    # ===============
    def get_users_form_data(self) -> UsersFormModel:
        return UsersFormModel(
            user_id=self.ui.user_id_users_input.text().strip(),
            username=self.ui.username_users_input.text().strip(),
            password=self.ui.password_users_input.text().strip(),
            role_id=self.ui.role_id_users_input.text().strip(),
            role_name=self.ui.role_name_users_input.text().strip(),
        )


    # Shows
    # ===============
    def show_users_data(self):
        # Disable Sorting to prevent data from being sorted
        self.users_table.setSortingEnabled(False)

        search_text = self.ui.filter_users_input.text().strip()
        search_text = search_text.lower() if search_text else None

        users_result = self.users_service.get_users(search_text)

        self.set_users_table_data(users_result.data)


    # Signal Handlers
    # ===============
    def handle_role_selected(self, role_data: dict):
        role_result = self.users_service.get_role_by_id(role_data['role_id'])
        if role_result.success and role_result.data:
            self.ui.role_id_users_input.setText(str(role_result.data.role_id))
            self.ui.role_name_users_input.setText(role_result.data.role_name)

    
    def handle_change_password(self, password_data: dict):
        user_id = self.ui.user_id_users_input.text().strip()
        result = self.users_service.change_password(user_id, password_data['old_password'], password_data['new_password'])
        
        if result.success:
            POSMessageBox.info(self, title=OK, message=result.message)
            self.show_users_data()

        else:
            POSMessageBox.error(self, title=ERR, message=result.message)


    # Event Listeners
    # ===============
    def on_user_selected(self):
        selected_row = self.users_table.selectedItems()
        if not selected_row:
            return
        
        row = selected_row[0].row()
        is_active = self.users_table.item(row, 3).text().strip() == 'Active'

        if is_active:
            self.ui.toggle_active_users_button.setText('Deactivate')
        else:
            self.ui.toggle_active_users_button.setText('Activate')


    def on_handle_role_enter(self):
        role_id = self.ui.role_id_users_input.text().strip()
        if not role_id:
            return

        # Try to find exact Supplier Id match
        result = self.users_service.get_role_by_id(role_id)
        if result.success and result.data:
            # Supplier found - fill the form
            self.handle_role_selected({'role_id': result.data.role_id})

        else:
            # Supplier not found - show dialog with filter
            self.roles_dialog.set_filter(role_id)
            self.roles_dialog.show()


    # Clears
    # ===============
    def clear_users_form_data(self):
        self.ui.user_id_users_input.clear()
        self.ui.username_users_input.clear()
        self.ui.password_users_input.clear()
        self.ui.role_id_users_input.clear()
        self.ui.role_name_users_input.clear()
        
        # Set the submit button text and connect to submit function
        self.ui.submit_users_button.setText('Submit')
        self.ui.submit_users_button.clicked.disconnect()
        self.ui.submit_users_button.clicked.connect(self.submit_users)


    # Setup Permissions
    # ===============
    def setup_permissions(self):
        self.ui.toggle_active_users_button.setVisible(
            self.permission_manager.has_permission(PERM_U_USERS)
        )
        self.ui.create_new_users_button.setVisible(
            self.permission_manager.has_permission(PERM_C_USERS)
        )
        self.ui.edit_users_button.setVisible(
            self.permission_manager.has_permission(PERM_U_USERS)
        )
        self.ui.delete_users_button.setVisible(
            self.permission_manager.has_permission(PERM_D_USERS)
        )
