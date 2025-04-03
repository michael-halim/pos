from PyQt6 import QtWidgets, QtCore
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt6.QtGui import QPainter, QFont, QPageLayout
from PyQt6.QtCore import Qt, QDateTime, QMarginsF, QSizeF
from PyQt6.QtGui import QPageSize

from response.response_message import ResponseMessage
from transactions.models.transactions_models import TransactionModel, TransactionTableItemModel
from generals.constants import (
    TAX_TABLE_KEY
) 
from helper import format_number, add_prefix
from generals.permission_manager import PermissionManager


class PrinterService:
    def __init__(self):
        self.printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
        self.printer.setPageLayout(QPageLayout(QPageSize(QSizeF(48, 100), QPageSize.Unit.Millimeter), QPageLayout.Orientation.Portrait, QMarginsF(2, 5, 2, 0)))
        self.permission_manager = PermissionManager()
        self.y_pos = 0
        self.left_margin = 2


    def show_preview(self, transaction_data: TransactionModel, detail_transactions: list[TransactionTableItemModel], customer_name: str | None) -> ResponseMessage:
        try:
            preview_dialog = QPrintPreviewDialog(self.printer)
            # Connect the preview dialog's paint request to our print_receipt method
            preview_dialog.paintRequested.connect(
                lambda printer: self.print_receipt(transaction_data=transaction_data, detail_transactions=detail_transactions, customer_name=customer_name)
            )
            
            # Show the preview dialog
            if preview_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                # Show print dialog after preview
                print_dialog = QPrintDialog(self.printer)
                if print_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                    pass
            
        except Exception as e:
            print(e)


    def print_receipt(self, transaction_data: TransactionModel, detail_transactions: list[TransactionTableItemModel], customer_name: str | None) -> ResponseMessage:
        current_datetime = QDateTime.currentDateTime()
        current_date = current_datetime.toString("dd-MMM-yyyy")
        
        painter = QPainter()
        painter.begin(self.printer)
        
        # Setup fonts
        title_font = QFont("Courier New", 12, QFont.Weight.Bold)
        normal_font = QFont("Courier New", 7)
        bold_font = QFont("Courier New", 7, QFont.Weight.Bold)
        
        # Get metrics for positioning
        rect = self.printer.pageRect(QPrinter.Unit.DevicePixel)
        width = int(rect.width())  # Convert to int
        
        # Start position
        y_pos = 10
        left_margin = 2
        
        # Draw header - use QRect instead of separate parameters
        painter.setFont(title_font)
        header_rect = QtCore.QRect(0, y_pos, width, 20)
        painter.drawText(header_rect, Qt.AlignmentFlag.AlignHCenter, "ELVES")
        y_pos += 30  # Increased space after title

        # Draw address with word wrapping
        painter.setFont(normal_font)
        address_text = "Jl. Dr. Ratulangi, Kota Palopo, Sulawesi Selatan"
        address_rect = QtCore.QRect(left_margin, y_pos, width - (left_margin * 2), 60)  # Increased height to 60
        painter.drawText(address_rect, Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap, address_text)

        # Calculate text height to properly advance y_pos
        text_rect = painter.boundingRect(address_rect, Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap, address_text)
        y_pos += text_rect.height() + 10  # Advance by actual text height plus padding


        painter.setFont(bold_font)
        painter.drawLine(left_margin, y_pos, width - left_margin, y_pos)
        y_pos += 15

        # Draw Cashier and Transactions Date
        painter.setFont(normal_font)

        cashier_text = f"Cashier: {self.permission_manager.get_username()}"
        painter.drawText(left_margin, y_pos, cashier_text)

        transactions_date_text = f"Date: {current_date}"
        transactions_date_width = painter.fontMetrics().horizontalAdvance(transactions_date_text)
        painter.drawText(width - transactions_date_width - left_margin, y_pos, transactions_date_text)
        y_pos += 15
        
        # Draw Customer Name if any
        if customer_name:
            customer_text = f"Customer: {customer_name}"
            painter.setFont(normal_font)
            painter.drawText(left_margin, y_pos, customer_text)
            y_pos += 15

        # Draw table header
        painter.setFont(bold_font)
        
        y_pos += 5

        painter.drawLine(left_margin, y_pos, width - left_margin, y_pos)
        
        y_pos += 15
        
        # Draw items
        painter.setFont(normal_font)
        
        # Use actual detail_transactions data
        for dt in detail_transactions:
            # Skip tax items
            if dt.sku == TAX_TABLE_KEY:
                continue
                
            # Get item data
            name = dt.product_name
            start_length, total_length = 0, len(name)

            # If name length > 32, then enter new line
            if total_length > 32:
                while total_length > 32:
                    min_length = min(total_length, start_length + 32)
                    painter.drawText(left_margin, y_pos, name[start_length:min_length])
                    y_pos += 15
                    start_length += min_length
                    total_length -= min_length
                    if total_length <= 32:
                        painter.drawText(left_margin, y_pos, name[start_length:])
                        break

            else:
                painter.drawText(left_margin, y_pos, name)
            
            y_pos += 15
            
            # Draw Unit x Price
            unit_price = f"{dt.qty} {dt.unit} x {format_number(dt.price)}"
            painter.drawText(left_margin, y_pos, unit_price)

            # Draw Subtotal
            total = format_number(dt.subtotal)
            total_width = painter.fontMetrics().horizontalAdvance(total)
            painter.drawText(width - total_width - left_margin, y_pos, total)
            
            y_pos += 15
        
        # Draw separator
        y_pos += 5
        painter.setFont(bold_font)
        painter.drawLine(left_margin, y_pos, width - left_margin, y_pos)
        y_pos += 15
        
        # Draw tax and total
        tax_text = "Tax:"
        painter.drawText(left_margin, y_pos, tax_text)

        tax_value = add_prefix(format_number(str(transaction_data.tax_amount)))
        tax_width = painter.fontMetrics().horizontalAdvance(tax_value)
        painter.drawText(width - tax_width - left_margin, y_pos, tax_value)

        y_pos += 15

        total_text = "Total:"
        painter.drawText(left_margin, y_pos, total_text)

        total_value = add_prefix(format_number(str(transaction_data.total_amount)))
        total_val_width = painter.fontMetrics().horizontalAdvance(total_value)
        painter.drawText(width - total_val_width - left_margin, y_pos, total_value)

        y_pos += 15

        change_text = "Change:"
        painter.drawText(left_margin, y_pos, change_text)


        change_value = add_prefix(format_number(str(transaction_data.payment_change)))
        change_val_width = painter.fontMetrics().horizontalAdvance(change_value)
        painter.drawText(width - change_val_width - left_margin, y_pos, change_value)

        y_pos += 25
        
        # Draw footer with word wrapping
        painter.setFont(normal_font)
        footer_text1 = "Barang yang sudah dibeli tidak dapat ditukar/dikembalikan"
        footer_text2 = "TERIMA KASIH ATAS KUNJUNGAN ANDA"
        
        # Create rectangle for first footer text
        footer1_rect = QtCore.QRect(left_margin, y_pos, width - (left_margin * 2), 60)
        painter.drawText(footer1_rect, Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap, footer_text1)
        
        # Calculate actual height of first text and advance y_pos
        text1_rect = painter.boundingRect(footer1_rect, Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap, footer_text1)
        y_pos += text1_rect.height() + 5  # Add small padding between texts
        
        # Create rectangle for second footer text
        footer2_rect = QtCore.QRect(left_margin, y_pos, width - (left_margin * 2), 60)
        painter.drawText(footer2_rect, Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap, footer_text2)

        painter.end()


    def add_new_line(self, increment: int) -> None:
        self.y_pos += increment
