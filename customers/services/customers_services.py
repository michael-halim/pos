from ..repositories.customers_repositories import CustomersRepository
from ..models.customers_models import CustomersModel

class CustomersService:
    def __init__(self):
        self.repository = CustomersRepository()


    def get_customers(self, search_text: str = None):
        return self.repository.get_customers(search_text)


    def get_customer_by_id(self, customer_id: int):
        return self.repository.get_customer_by_id(customer_id)


    def create_customer(self, customer_data: CustomersModel):
        return self.repository.create_customer(customer_data)


    def update_customer(self, customer_data: CustomersModel):
        return self.repository.update_customer(customer_data)
    

    def delete_customer_by_customer_id(self, customer_id: int):
        return self.repository.delete_customer_by_customer_id(customer_id)
    