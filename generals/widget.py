from PyQt6 import QtWidgets, QtCore
from generals.fonts import POSFonts

def create_checkbox_item(_id: str, is_editable: bool = False, size: int = 12) -> QtWidgets.QTableWidgetItem:
    checkbox_item = QtWidgets.QTableWidgetItem()
    checkbox_item.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
    checkbox_item.setData(QtCore.Qt.ItemDataRole.UserRole, _id)
    checkbox_item.setFont(POSFonts.get_font(size=size))
    
    if not is_editable:
        checkbox_item.setFlags(QtCore.Qt.ItemFlag.ItemIsEditable)

    return checkbox_item


