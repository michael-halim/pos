from PyQt6 import QtGui
from PyQt6.QtPrintSupport import QPrinter
from stock_opname.repositories.stock_opname_repositories import StockOpnameRepository
from stock_opname.models.stock_opname_models import StockOpnameModel
from response.response_message import ResponseMessage
from stock_opname.services.stock_opname_export import HEADER_HTML_WITH_CURRENT_STOCK, HEADER_HTML_NO_CURRENT_STOCK, FOOTER_HTML
from threads.thread_service import ThreadManager
from openpyxl import Workbook
from exports.export_service import ExportService

class StockOpnameService:
    def __init__(self):
        self.repository = StockOpnameRepository()
        self.thread_manager = ThreadManager()
        self.export_service = ExportService()

    def get_stock_opname(self, search_text: str = None):
        return self.repository.get_stock_opname(search_text)


    def export_pdf(self, stock_opname_data: list[StockOpnameModel], file_path: str, on_complete=None, on_error=None, on_progress=None):
        self.thread_manager.run_in_thread(
            self.export_pdf_task,
            on_complete,
            on_error,
            on_progress,
            stock_opname_data,
            file_path
        )


    def export_pdf_task(self, stock_opname_data: list[StockOpnameModel], file_path: str):
        # Create HTML content for stock opname with column current stock and no stock
        html = HEADER_HTML_WITH_CURRENT_STOCK
        html_no_stock = HEADER_HTML_NO_CURRENT_STOCK

        # Add table data
        for stock_opname in stock_opname_data:
            html += "<tr>"
            html += f"<td style='border: 1px solid black; padding: 8px; text-align: left;'>{stock_opname.sku}</td>"
            html += f"<td style='border: 1px solid black; padding: 8px; text-align: left;'>{stock_opname.product_name}</td>"
            html += f"<td style='border: 1px solid black; padding: 8px; text-align: left;'>{stock_opname.qty}</td>"
            html += f"<td style='border: 1px solid black; padding: 8px; text-align: left;'>{stock_opname.unit}</td>"
            html += "<td style='border: 1px solid black; padding: 8px; text-align: left;'></td></tr>"

            html_no_stock += '<tr>'
            html_no_stock += f"<td style='border: 1px solid black; padding: 8px; text-align: left;'>{stock_opname.sku}</td>"
            html_no_stock += f"<td style='border: 1px solid black; padding: 8px; text-align: left;'>{stock_opname.product_name}</td>"
            html_no_stock += f"<td style='border: 1px solid black; padding: 8px; text-align: left;'>{stock_opname.unit}</td>"
            html_no_stock += "<td style='border: 1px solid black; padding: 8px; text-align: left;'></td></tr>"
        
        html += FOOTER_HTML
        html_no_stock += FOOTER_HTML
        
        result_pdf = self.export_service.export_to_pdf(html, file_path)

        file_path_no_stock = file_path.replace("stock_opname_", "stock_opname_no_stock_")
        result_pdf_no_stock = self.export_service.export_to_pdf(html_no_stock, file_path_no_stock)

        if not result_pdf.success:
            return ResponseMessage.error(message=result_pdf.message)
        
        if not result_pdf_no_stock.success:
            return ResponseMessage.error(message=result_pdf_no_stock.message)

        return ResponseMessage.ok(message=f"PDF saved successfully to:\n{file_path}\n{file_path_no_stock}")
    

    def export_excel(self, data: list[StockOpnameModel], file_path: str, on_complete=None, on_error=None, on_progress=None):
        self.thread_manager.run_in_thread(
            self.export_excel_task,
            on_complete,
            on_error,
            on_progress,
            data,
            file_path
        )


    def export_excel_task(self, data: list[StockOpnameModel], file_path: str):
        # Create workbook
        workbook = Workbook()
        sheet = workbook.active

        # Add headers
        sheet.append(["SKU", "Product Name", "Current Stock", "Unit"])

        # Add data
        for stock_opname in data:
            sheet.append([stock_opname.sku, stock_opname.product_name, stock_opname.qty, stock_opname.unit])

        # Save workbook
        workbook.save(file_path)

        return ResponseMessage.ok(message=f"Excel saved successfully to:\n{file_path}")
