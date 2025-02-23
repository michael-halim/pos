from PyQt6 import QtWidgets, uic, QtCore, QtGui

from role_permissions.services.role_permissions_services import RolePermissionsService
from role_permissions.models.role_permissions_models import RolesModel, PermissionsModel

from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS
from generals.build import resource_path
from generals.widget import create_checkbox_item

class RolePermissionsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/role_permissions.ui'), self)

        # Init Services
        self.role_permissions_service = RolePermissionsService()

        # Init Table
        self.roles_table = self.ui.roles_table
        self.permissions_table = self.ui.permissions_table
        self.roles_table.setSortingEnabled(True)
        self.permissions_table.setSortingEnabled(True)
        
        # Connect search input to filter function
        self.ui.filter_roles_input.textChanged.connect(self.show_roles_data)
        self.ui.filter_permissions_input.textChanged.connect(self.show_permissions_data)
        self.ui.cancel_role_permissions_button.clicked.connect(self.cancel_role_permissions)
        self.ui.create_new_role_permissions_button.clicked.connect(self.create_new_role_permissions)
        self.ui.edit_role_permissions_button.clicked.connect(self.edit_role_permissions)
        self.ui.delete_role_permissions_button.clicked.connect(self.delete_role_permissions)
        self.ui.submit_role_permissions_button.clicked.connect(self.submit_role_permissions)
        
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
        
        # Change the background color of the checkbox when clicked
        self.permissions_table.itemChanged.connect(self.on_checkbox_clicked)

        self.show_roles_data()


    def cancel_role_permissions(self):
        self.clear_roles_form_data()
        self.set_enabled_roles_form_group(False)
        self.set_enabled_roles_group_buttons(True)
        self.set_permissions_table_data([], set(), is_editable=False)

        self.ui.submit_role_permissions_button.setText('Submit')
        self.ui.submit_role_permissions_button.clicked.disconnect()
        self.ui.submit_role_permissions_button.clicked.connect(self.submit_role_permissions)


    def create_new_role_permissions(self):
        self.clear_roles_form_data()
        self.set_enabled_roles_form_group(True)
        self.set_enabled_roles_group_buttons(False)
        self.set_permissions_table_data([], set(), is_editable=True)

        permissions = self.role_permissions_service.get_permissions()

        self.set_permissions_table_data(permissions.data, set(), is_editable=True)


    def edit_role_permissions(self):
        selected_row = self.roles_table.selectedItems()
        if not selected_row:
            POSMessageBox.error(self, title='Error', message="Please select a role to edit")
            return
        
        self.set_enabled_roles_form_group(True)
        self.set_enabled_roles_group_buttons(False)

        row = selected_row[0].row()
        role_id = self.roles_table.item(row, 0).text()

        permissions = self.role_permissions_service.get_permissions()
        allowed_permissions = self.role_permissions_service.get_permissions_by_role_id(role_id)

        self.set_permissions_table_data(permissions.data, allowed_permissions.data, is_editable=True)

        role = self.get_selected_roles_table_data()

        self.set_roles_form_data(role)

        self.ui.submit_role_permissions_button.setText('Update')
        self.ui.submit_role_permissions_button.clicked.disconnect()
        self.ui.submit_role_permissions_button.clicked.connect(self.update_role_permissions)


    def update_role_permissions(self):
        roles_form_data: RolesModel = self.get_roles_form_data()
        role_id = self.ui.role_id_role_permissions_input.text().strip()
        roles_form_data.role_id = role_id

        if not roles_form_data.role_name:
            POSMessageBox.error(self, title='Error', message="Role name is required")
            return
        
        past_permissions_result = self.role_permissions_service.get_permissions_by_role_id(role_id)
        current_permissions = self.get_selected_permissions_table_data()

        added_data = current_permissions - past_permissions_result.data
        deleted_data = past_permissions_result.data - current_permissions

        result = self.role_permissions_service.update_role_permissions(roles_form_data, added_data, deleted_data)
        if result.success:
            POSMessageBox.info(self, title='Success', message=result.message)

            self.roles_table.setRowCount(0)
            self.permissions_table.setRowCount(0)
            self.set_enabled_roles_form_group(False)
            self.set_enabled_roles_group_buttons(True)
            self.clear_roles_form_data()
            self.show_roles_data()

        else:
            POSMessageBox.error(self, title='Error', message=result.message)


        self.ui.submit_role_permissions_button.setText('Submit')
        self.ui.submit_role_permissions_button.clicked.disconnect()
        self.ui.submit_role_permissions_button.clicked.connect(self.submit_role_permissions)


    def delete_role_permissions(self):
        selected_row = self.roles_table.selectedItems()
        if not selected_row:
            POSMessageBox.error(self, title='Error', message="Please select a role to delete")
            return
        
        confirm = POSMessageBox.confirm(
                        self, title='Confirm Deletion', 
                        message='Are you sure you want to delete this role?')

        if confirm:
            row = selected_row[0].row()
            role_id = self.roles_table.item(row, 0).text()

            result = self.role_permissions_service.delete_role_permissions_by_role_id(role_id)
            if result.success:
                POSMessageBox.info(self, title='Success', message=result.message)

                self.roles_table.setRowCount(0)
                self.permissions_table.setRowCount(0)
                self.set_enabled_roles_form_group(False)
                self.set_enabled_roles_group_buttons(True)
                self.clear_roles_form_data()
                self.show_roles_data()

            else:
                POSMessageBox.error(self, title='Error', message=result.message)


    def submit_role_permissions(self):
        roles_form_data: RolesModel = self.get_roles_form_data()
        if not roles_form_data.role_name:
            POSMessageBox.error(self, title='Error', message="Role name is required")
            return
        
        selected_permissions: set[str] = self.get_selected_permissions_table_data()

        result = self.role_permissions_service.submit_role_permissions(roles_form_data, selected_permissions)
        if result.success:
            POSMessageBox.info(self, title='Success', message=result.message)
            
            self.roles_table.setRowCount(0)
            self.permissions_table.setRowCount(0)
            self.set_enabled_roles_form_group(False)
            self.set_enabled_roles_group_buttons(True)
            self.clear_roles_form_data()
            self.show_roles_data()

        else:
            POSMessageBox.error(self, title='Error', message=result.message)
    

    # Overrides
    # ===============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        # Refresh the data
        self.show_roles_data()


    def show(self):
        """Override show to ensure data is refreshed"""
        super().show()
        # Refresh the data
        self.show_roles_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
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


    def set_roles_form_data(self, data: RolesModel):
        self.ui.role_id_role_permissions_input.setText(data.role_id)
        self.ui.role_name_role_permissions_input.setText(data.role_name)
        self.ui.role_description_role_permissions_input.setText(data.role_description)


    def set_permissions_table_data(self, data: list[PermissionsModel], 
                                   allowed_permissions: set[str], 
                                   is_editable: bool = False):
        # Clear the table
        self.permissions_table.setRowCount(0)

        for permission in data:
            current_row = self.permissions_table.rowCount()
            self.permissions_table.insertRow(current_row)

            permission_id = str(permission.permission_id)

            # Create checkbox item
            checkbox_item = create_checkbox_item(permission_id, is_editable=is_editable, size=22)

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


    def set_enabled_roles_form_group(self, is_enabled: bool):
        self.ui.role_name_role_permissions_input.setEnabled(is_enabled)
        self.ui.role_description_role_permissions_input.setEnabled(is_enabled)
        self.ui.submit_role_permissions_button.setEnabled(is_enabled)
        self.ui.cancel_role_permissions_button.setEnabled(is_enabled)
        self.ui.role_name_role_permissions_input.setClearButtonEnabled(not is_enabled)


    def set_enabled_roles_group_buttons(self, is_enabled: bool):
        self.ui.create_new_role_permissions_button.setEnabled(is_enabled)
        self.ui.edit_role_permissions_button.setEnabled(is_enabled)
        self.ui.delete_role_permissions_button.setEnabled(is_enabled)
        self.ui.roles_table.setEnabled(is_enabled)


    # Getters
    # ===============
    def get_roles_form_data(self) -> RolesModel:
        role_name = self.ui.role_name_role_permissions_input.text().strip()
        role_description = self.ui.role_description_role_permissions_input.toPlainText().strip()

        return RolesModel(
            role_id='',
            role_name=role_name,
            role_description=role_description,
        )
    

    def get_selected_roles_table_data(self) -> RolesModel:
        selected_row = self.roles_table.selectedItems()
        if not selected_row:
            return None
        
        row = selected_row[0].row()

        role_id = self.roles_table.item(row, 0).text()
        role_name = self.roles_table.item(row, 1).text()
        role_description = self.roles_table.item(row, 2).text()

        return RolesModel(
            role_id=role_id,
            role_name=role_name,
            role_description=role_description,
        )


    def get_selected_permissions_table_data(self) -> set[str]:
        selected_permissions = set()
        for row in range(self.permissions_table.rowCount()):
            checkbox_item = self.permissions_table.item(row, 0)

            if checkbox_item and checkbox_item.checkState() == QtCore.Qt.CheckState.Checked:
                selected_permissions.add(checkbox_item.data(QtCore.Qt.ItemDataRole.UserRole))

        return selected_permissions


    # Shows
    # ===============
    def show_roles_data(self):
        search_text = self.ui.filter_roles_input.text().strip()
        search_text = search_text.lower() if search_text else None

        roles_result = self.role_permissions_service.get_roles(search_text)

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
            permissions = self.role_permissions_service.get_permissions()

            # Get Allowed Permissions
            allowed_permissions = self.role_permissions_service.get_permissions_by_role_id(role_id)
        
            self.set_permissions_table_data(permissions.data, allowed_permissions.data)


    def on_permission_selected(self):
        selected_rows = self.permissions_table.selectedItems()
        if selected_rows:
            self.current_selected_permission = selected_rows[0].row()


    def on_checkbox_clicked(self, item):
        if item.column() == 0:
            row = item.row()
            is_checked = item.checkState() == QtCore.Qt.CheckState.Checked
            
            # Update the row background color based on checkbox state
            new_color = QtGui.QColor(0xD1, 0xE7, 0xDD) if is_checked else QtGui.QColor(0xF8, 0xD7, 0xDA)
            
            # Update background color for all cells in the row
            for col in range(self.permissions_table.columnCount()):
                cell_item = self.permissions_table.item(row, col)
                if cell_item:
                    cell_item.setBackground(new_color)


    # Clears
    # ===============
    def clear_roles_form_data(self):
        self.ui.role_id_role_permissions_input.clear()
        self.ui.role_name_role_permissions_input.clear()
        self.ui.role_description_role_permissions_input.clear()
