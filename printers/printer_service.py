from PyQt6.QtPrintSupport import QPrinter
from PyQt6 import QtGui

from response.response_message import ResponseMessage

class PrinterService:
    @staticmethod
    def print_receipt(html_content: str, file_path: str) -> ResponseMessage:
        """Print Receipt to printer"""
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setPageOrientation(QtGui.QPageLayout.Orientation.Portrait)
            
            document = QtGui.QTextDocument()
            document.setHtml(html_content)
            document.print(printer)

            return ResponseMessage.ok(message=f"Receipt printed successfully to:\n{file_path}")
        
        except Exception as e:
            return ResponseMessage.error(message=f"Receipt print failed: {str(e)}") 