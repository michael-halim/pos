from typing import List, Optional
from ..repositories.import_products_dialog_repositories import ImportProductsDialogRepository

class ImportProductsDialogService:
    def __init__(self):
        self.repository = ImportProductsDialogRepository()
