from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class ResponseMessage:
    success: bool
    message: str
    data: Optional[Any] = None

    @classmethod
    def ok(cls, message: str = "Success", data: Any = None) -> 'ResponseMessage':
        return cls(success=True, message=message, data=data)

    @classmethod
    def fail(cls, message: str) -> 'ResponseMessage':
        return cls(success=False, message=message) 