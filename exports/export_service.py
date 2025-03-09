from PyQt6.QtPrintSupport import QPrinter
from PyQt6 import QtGui
from response.response_message import ResponseMessage

class ExportService:
    @staticmethod
    def export_to_pdf(html_content: str, file_path: str) -> ResponseMessage:
        """Export data to PDF file"""
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setPageOrientation(QtGui.QPageLayout.Orientation.Portrait)
            
            document = QtGui.QTextDocument()
            document.setHtml(html_content)
            document.print(printer)

            return ResponseMessage.ok(message=f"PDF saved successfully to:\n{file_path}")
        
        except Exception as e:
            return ResponseMessage.error(message=f"Export failed: {str(e)}") 