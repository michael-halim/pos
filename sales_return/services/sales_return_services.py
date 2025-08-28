from sales_return.models.sales_return_models import SalesReturnModel, DetailSalesReturnModel
from sales_return.repositories.sales_return_repositories import SalesReturnRepository

from response.response_message import ResponseMessage
from generals.constants import PERM_C_SALES_RETURN, PERM_U_SALES_RETURN
from generals.messages import ERR_PERM_C_SALES_RETURN, ERR_PERM_U_SALES_RETURN
from generals.permission_manager import PermissionManager


class SalesReturnService:
    def __init__(self):
        self.repository = SalesReturnRepository()
        self.permission_manager = PermissionManager()


    def get_customer_by_id(self, customer_id: str):
        return self.repository.get_customer_by_id(customer_id)
    
    
    def get_product_by_sku(self, sku: str):
        return self.repository.get_product_by_sku(sku)
    

    def get_product_unit_details(self, sku: str):
        return self.repository.get_product_unit_details(sku)
    

    def create_sales_return_id(self):
        return self.repository.create_sales_return_id()
    

    def submit_sales_return(self, sales_return_data: SalesReturnModel, detail_sales_return_data: list[DetailSalesReturnModel]):
        if not self.permission_manager.has_permission(PERM_C_SALES_RETURN):
            return ResponseMessage.fail(message=ERR_PERM_C_SALES_RETURN)
        
        return self.repository.submit_sales_return(sales_return_data, detail_sales_return_data)
    

    def update_sales_return(self, sales_return_data: SalesReturnModel, added_detail_sales_return: 
                               list[DetailSalesReturnModel], 
                               updated_detail_sales_return: list[DetailSalesReturnModel], 
                               deleted_detail_sales_return: list[DetailSalesReturnModel]):
        if not self.permission_manager.has_permission(PERM_U_SALES_RETURN):
            return ResponseMessage.fail(message=ERR_PERM_U_SALES_RETURN)
        
        return self.repository.update_sales_return(sales_return_data, added_detail_sales_return, 
                                                      updated_detail_sales_return, deleted_detail_sales_return)
    

    def get_detail_sales_return_by_id(self, sales_return_id: str):
        return self.repository.get_detail_sales_return_by_id(sales_return_id)
    

    def get_sales_return_by_id(self, sales_return_id: str):
        return self.repository.get_sales_return_by_id(sales_return_id)