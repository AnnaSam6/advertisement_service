from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AdvertisementBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Заголовок объявления")
    description: str = Field(..., min_length=1, max_length=1000, description="Описание")
    price: float = Field(..., gt=0, description="Цена (должна быть больше 0)")
    author: str = Field(..., min_length=1, max_length=100, description="Автор объявления")

class AdvertisementCreate(AdvertisementBase):
    """Схема для создания объявления"""
    pass

class AdvertisementUpdate(BaseModel):
    """Схема для обновления (все поля опциональны)"""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    author: Optional[str] = Field(None, min_length=1, max_length=100)

class AdvertisementInDB(AdvertisementBase):
    """Полная модель объявления из БД"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
