from dialogs.products_dialog.repositories.products_dialog_repositories import ProductsDialogRepository

class ProductsDialogService:
    def __init__(self):
        self.repository = ProductsDialogRepository()


    def get_products(self, search_text: str = None, limit: int = 100):
        return self.repository.get_products(search_text, limit)

