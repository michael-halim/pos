from customers.repositories.customers_repositories import CustomersRepository
from customers.models.customers_models import CustomersModel

from generals.permission_manager import PermissionManager
from generals.constants import PERM_R_CUSTOMERS, PERM_C_CUSTOMERS, PERM_U_CUSTOMERS, PERM_D_CUSTOMERS
from generals.messages import ERR_PERM_R_CUSTOMERS, ERR_PERM_C_CUSTOMERS, ERR_PERM_U_CUSTOMERS, ERR_PERM_D_CUSTOMERS

from response.response_message import ResponseMessage

class CustomersService:
    def __init__(self):
        self.repository = CustomersRepository()
        self.permission_manager = PermissionManager()


    def get_customers(self, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_CUSTOMERS):
            return ResponseMessage.fail(message=ERR_PERM_R_CUSTOMERS)

        return self.repository.get_customers(search_text)


    def get_customer_by_id(self, customer_id: int):
        if not self.permission_manager.has_permission(PERM_R_CUSTOMERS):
            return ResponseMessage.fail(message=ERR_PERM_R_CUSTOMERS)

        return self.repository.get_customer_by_id(customer_id)


    def create_customer(self, customer_data: CustomersModel):
        if not self.permission_manager.has_permission(PERM_C_CUSTOMERS):
            return ResponseMessage.fail(message=ERR_PERM_C_CUSTOMERS)

        return self.repository.create_customer(customer_data)


    def update_customer(self, customer_data: CustomersModel):
        if not self.permission_manager.has_permission(PERM_U_CUSTOMERS):
            return ResponseMessage.fail(message=ERR_PERM_U_CUSTOMERS)

        return self.repository.update_customer(customer_data)
    

    def delete_customer_by_customer_id(self, customer_id: int): 
        if not self.permission_manager.has_permission(PERM_D_CUSTOMERS):
            return ResponseMessage.fail(message=ERR_PERM_D_CUSTOMERS)

        return self.repository.delete_customer_by_customer_id(customer_id)
    