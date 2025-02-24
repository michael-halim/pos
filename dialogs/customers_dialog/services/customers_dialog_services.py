from ..repositories.customers_dialog_repositories import CustomersDialogRepository

class CustomersDialogService:
    def __init__(self):
        self.repository = CustomersDialogRepository()


    def get_customers(self, search_text: str = None):
        return self.repository.get_customers(search_text)
