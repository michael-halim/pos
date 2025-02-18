from PyQt6.QtWidgets import QHeaderView, QAbstractItemView, QTableWidget
from PyQt6.QtWidgets import QDateEdit


RESIZE_TO_CONTENTS = QHeaderView.ResizeMode.ResizeToContents
SELECT_ROWS = QAbstractItemView.SelectionBehavior.SelectRows
SINGLE_SELECTION = QAbstractItemView.SelectionMode.SingleSelection
NO_EDIT_TRIGGERS = QTableWidget.EditTrigger.NoEditTriggers
DATE_EDIT_NO_BUTTONS = QDateEdit.ButtonSymbols.NoButtons

DATE_FORMAT_DDMMYYYY = "dd/MM/yyyy"