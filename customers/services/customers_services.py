from typing import List, Optional
from ..repositories.customers_repositories import CustomersRepository

class CustomersService:
    def __init__(self):
        self.repository = CustomersRepository()
