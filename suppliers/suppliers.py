from PyQt6 import QtWidgets, uic
from generals.build import resource_path

from suppliers.services.suppliers_services import SuppliersService  
from suppliers.models.suppliers_models import SuppliersModel

from generals.fonts import POSFonts
from generals.permission_manager import PermissionManager
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    PERM_R_SUPPLIERS, PERM_C_SUPPLIERS, PERM_U_SUPPLIERS, PERM_D_SUPPLIERS,
) 
from generals.messages import (
    ERR, ERR_PERM_R_SUPPLIERS, ERR_PERM_C_SUPPLIERS, ERR_PERM_U_SUPPLIERS, ERR_PERM_D_SUPPLIERS, PERM_DENIED, OK
)
from generals.message_box import POSMessageBox


class SuppliersWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_SUPPLIERS):
            POSMessageBox.error(self, title=ERR, message=ERR_PERM_R_SUPPLIERS)
            return

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/suppliers.ui'), self)
        
        # Setup permissions
        self.setup_permissions()

        # Init Services
        self.suppliers_service = SuppliersService()

        # Connect Add Supplier Button
        self.ui.add_supplier_button.clicked.connect(self.add_supplier)
        self.ui.edit_supplier_button.clicked.connect(self.edit_supplier)
        self.ui.delete_supplier_button.clicked.connect(self.delete_supplier)
        self.ui.close_supplier_button.clicked.connect(lambda: self.close())
        self.ui.clear_supplier_button.clicked.connect(self.clear_supplier_form_data)
        self.ui.submit_supplier_button.clicked.connect(self.submit_supplier)

        # Connect search input to filter function
        self.ui.supplier_filter_input.textChanged.connect(self.show_suppliers_data)
        
        # Set table properties
        self.ui.suppliers_table.setSelectionBehavior(SELECT_ROWS)
        self.ui.suppliers_table.setSelectionMode(SINGLE_SELECTION)

        self.ui.suppliers_table.setEditTriggers(NO_EDIT_TRIGGERS)

        self.ui.suppliers_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.ui.suppliers_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        # Show data for both tables
        self.show_suppliers_data()
    

    # Overrides
    # ===============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_R_SUPPLIERS):
            POSMessageBox.error(self, title=ERR, message=ERR_PERM_R_SUPPLIERS)
            self.close()
            return
        
        # Refresh the data
        self.show_suppliers_data()


    def show(self):
        """Override show to ensure data is refreshed"""
        super().show()
        if not self.permission_manager.has_permission(PERM_R_SUPPLIERS):
            POSMessageBox.error(self, title=ERR, message=ERR_PERM_R_SUPPLIERS)
            return

        # Refresh the data
        self.show_suppliers_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_R_SUPPLIERS):
            POSMessageBox.error(self, title=ERR, message=ERR_PERM_R_SUPPLIERS)
            return

        # Refresh the data
        self.show_suppliers_data()


    def add_supplier(self):
        if not self.permission_manager.has_permission(PERM_C_SUPPLIERS):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_C_SUPPLIERS)
            return

        self.clear_supplier_form_data()
        self.ui.submit_supplier_button.setText("Submit")
        self.ui.submit_supplier_button.clicked.disconnect()
        self.ui.submit_supplier_button.clicked.connect(self.submit_supplier)
        self.toggle_suppliers_form(True)


    def submit_supplier(self):
        if not self.permission_manager.has_permission(PERM_C_SUPPLIERS):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_C_SUPPLIERS)
            return

        supplier_form_data: SuppliersModel = self.get_supplier_form_data()
        if not supplier_form_data.supplier_name:
            POSMessageBox.error(self, title=ERR, message="Please fill all required fields")
            return
        
        result = self.suppliers_service.submit_supplier(supplier_form_data)
        if result.success:
            POSMessageBox.info(self, title=OK, message=result.message)
            
            self.clear_supplier_form_data()
            self.show_suppliers_data()
            
        else:
            POSMessageBox.error(self, title=ERR, message=result.message)


    def edit_supplier(self):
        if not self.permission_manager.has_permission(PERM_U_SUPPLIERS):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_U_SUPPLIERS)
            return

        selected_row = self.ui.suppliers_table.selectedItems()
        if not selected_row:
            POSMessageBox.error(self, title=ERR, message="Please select a supplier to edit")
            return
        
        row = selected_row[0].row()
        supplier_id = self.ui.suppliers_table.item(row, 0).text()
        

        supplier_result = self.suppliers_service.get_supplier_by_id(supplier_id)
        if not supplier_result.success:
            POSMessageBox.error(self, title=ERR, message=supplier_result.message)
            return

        self.set_supplier_form_data(supplier_result.data)
        self.toggle_suppliers_form(True)

        self.ui.submit_supplier_button.setText('Update')
        self.ui.submit_supplier_button.clicked.disconnect()
        self.ui.submit_supplier_button.clicked.connect(self.update_supplier)


    def update_supplier(self):
        if not self.permission_manager.has_permission(PERM_U_SUPPLIERS):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_U_SUPPLIERS)
            return

        supplier_form_data: SuppliersModel = self.get_supplier_form_data()
        supplier_id = self.ui.supplier_id_input.text().strip()
        supplier_form_data.supplier_id = supplier_id

        if not supplier_form_data.supplier_name:
            POSMessageBox.error(self, title=ERR, message="Supplier name is required")
            return
        
        result = self.suppliers_service.update_supplier(supplier_form_data)
        if result.success:
            POSMessageBox.info(self, title=OK, message=result.message)

            self.ui.suppliers_table.setRowCount(0)
            self.clear_supplier_form_data()
            self.show_suppliers_data()

        else:
            POSMessageBox.error(self, title=ERR, message=result.message)


        self.ui.submit_supplier_button.setText('Submit')
        self.ui.submit_supplier_button.clicked.disconnect()
        self.ui.submit_supplier_button.clicked.connect(self.submit_supplier)

    
    def delete_supplier(self):
        if not self.permission_manager.has_permission(PERM_D_SUPPLIERS):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_D_SUPPLIERS)
            return

        selected_row = self.ui.suppliers_table.selectedItems()
        if not selected_row:
            POSMessageBox.error(self, title=ERR, message="Please select a supplier to delete")
            return
        
        confirm = POSMessageBox.confirm(
                        self, title='Confirm Deletion', 
                        message='Are you sure you want to delete this supplier ?')

        if confirm:
            row = selected_row[0].row()
            supplier_id = self.ui.suppliers_table.item(row, 0).text()

            result = self.suppliers_service.delete_supplier_by_id(supplier_id)
            if result.success:
                POSMessageBox.info(self, title=OK, message=result.message)

                self.ui.suppliers_table.setRowCount(0)
                self.clear_supplier_form_data()
                self.show_suppliers_data()

            else:
                POSMessageBox.error(self, title=ERR, message=result.message)


    # Setters
    # ===============
    def set_supplier_form_data(self, supplier: SuppliersModel):
        self.ui.supplier_id_input.setText(str(supplier.supplier_id))
        self.ui.supplier_name_input.setText(str(supplier.supplier_name))
        self.ui.supplier_address_input.setText(str(supplier.supplier_address))
        self.ui.supplier_phone_number_input.setText(str(supplier.supplier_phone))
        self.ui.supplier_city_input.setText(str(supplier.supplier_city))
        self.ui.supplier_remarks_input.setText(str(supplier.supplier_remarks))


    def set_suppliers_table_data(self, suppliers: list[SuppliersModel]):
        # Clear the table
        self.ui.suppliers_table.setRowCount(0)

        for supplier in suppliers:
            current_row = self.ui.suppliers_table.rowCount()
            self.ui.suppliers_table.insertRow(current_row)

            table_items =  [ 
                QtWidgets.QTableWidgetItem(str(supplier.supplier_id)),
                QtWidgets.QTableWidgetItem(supplier.supplier_name),
                QtWidgets.QTableWidgetItem(supplier.supplier_address),
                QtWidgets.QTableWidgetItem(supplier.supplier_phone),
                QtWidgets.QTableWidgetItem(supplier.supplier_city),
                QtWidgets.QTableWidgetItem(supplier.supplier_remarks),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.ui.suppliers_table.setItem(current_row, col, item)
        
        self.ui.suppliers_table.setSortingEnabled(True)


    # Getters
    # ===============
    def get_supplier_form_data(self) -> SuppliersModel:
        supplier_id = self.ui.supplier_id_input.text().strip() if self.ui.supplier_id_input.text().strip() else ''
        supplier_name = self.ui.supplier_name_input.text().strip().upper() if self.ui.supplier_name_input.text().strip() else ''    
        supplier_address = self.ui.supplier_address_input.text().strip().upper() if self.ui.supplier_address_input.text().strip() else ''
        supplier_phone = self.ui.supplier_phone_number_input.text().strip() if self.ui.supplier_phone_number_input.text().strip() else ''
        supplier_city = self.ui.supplier_city_input.text().strip().upper() if self.ui.supplier_city_input.text().strip() else ''
        supplier_remarks = self.ui.supplier_remarks_input.toPlainText().strip() if self.ui.supplier_remarks_input.toPlainText().strip() else ''

        return SuppliersModel(supplier_id=supplier_id, supplier_name=supplier_name, 
                                supplier_address=supplier_address, supplier_phone=supplier_phone, 
                                supplier_city=supplier_city, supplier_remarks=supplier_remarks)


    # Shows
    # ===============
    def show_suppliers_data(self):
        # Temporarily disable sorting
        self.ui.suppliers_table.setSortingEnabled(False)

        search_text = self.ui.supplier_filter_input.text().strip()
        search_text = search_text.upper() if search_text else None

        suppliers_result = self.suppliers_service.get_suppliers(search_text)

        self.set_suppliers_table_data(suppliers_result.data)


    # Toggles
    # ===============
    def toggle_suppliers_form(self, mode: bool = True):
        self.ui.supplier_address_label.setEnabled(mode)
        self.ui.supplier_address_input.setEnabled(mode)
        self.ui.supplier_name_label.setEnabled(mode)
        self.ui.supplier_name_input.setEnabled(mode)
        self.ui.supplier_phone_number_label.setEnabled(mode)
        self.ui.supplier_phone_number_input.setEnabled(mode)
        self.ui.supplier_city_label.setEnabled(mode)
        self.ui.supplier_city_input.setEnabled(mode)
        self.ui.supplier_remarks_label.setEnabled(mode)
        self.ui.supplier_remarks_input.setEnabled(mode)
        self.ui.clear_supplier_button.setEnabled(mode)
        self.ui.submit_supplier_button.setEnabled(mode)


    # Clears
    # ===============
    def clear_supplier_form_data(self):
        self.ui.supplier_id_input.clear()
        self.ui.supplier_name_input.clear()
        self.ui.supplier_address_input.clear()
        self.ui.supplier_phone_number_input.clear()
        self.ui.supplier_city_input.clear()
        self.ui.supplier_remarks_input.clear()


    def setup_permissions(self):
        self.ui.add_supplier_button.setVisible(self.permission_manager.has_permission(PERM_C_SUPPLIERS))
        self.ui.edit_supplier_button.setVisible(self.permission_manager.has_permission(PERM_U_SUPPLIERS))
        self.ui.delete_supplier_button.setVisible(self.permission_manager.has_permission(PERM_D_SUPPLIERS))

