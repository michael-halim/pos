from dataclasses import dataclass
from datetime import datetime

@dataclass
class LogsModel:
    created_at: datetime
    log_type: str
    log_description: str
    old_data: str
    new_data: str
    created_by: str
