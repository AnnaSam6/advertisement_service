from pydantic import BaseModel
from typing import Optional

class AdvertisementResponse(BaseModel):
    """Схема для ответа API"""
    id: int
    title: str
    description: str
    price: float
    author: str
    created_at: str  # ISO формат строки

    class Config:
        from_attributes = True

class PaginationParams(BaseModel):
    """Параметры пагинации"""
    limit: int = 10
    offset: int = 0
