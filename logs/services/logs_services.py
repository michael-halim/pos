from typing import List, Optional
from ..repositories.logs_repositories import LogsRepository

class LogsService:
    def __init__(self):
        self.repository = LogsRepository()
