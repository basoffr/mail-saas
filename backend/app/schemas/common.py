from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class DataResponse(BaseModel, Generic[T]):
    data: Optional[T] = None
    error: Optional[str] = None
