from typing import List, Optional
from ..repositories.categories_dialog_repositories import CategoriesDialogRepository

class CategoriesDialogService:
    def __init__(self):
        self.repository = CategoriesDialogRepository()


    def get_categories(self, search_text: str = None):
        return self.repository.get_categories(search_text)
