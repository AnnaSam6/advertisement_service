from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

# ========== Базовые схемы ==========

class AdvertisementBase(BaseModel):
    """Базовая схема с общими полями"""
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="Заголовок объявления"
    )
    description: str = Field(
        ..., 
        min_length=1, 
        max_length=1000, 
        description="Описание объявления"
    )
    price: float = Field(
        ..., 
        gt=0, 
        description="Цена (должна быть больше 0)"
    )
    author: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="Автор объявления"
    )

# ========== Схема для создания ==========

class AdvertisementCreate(AdvertisementBase):
    """Схема для POST запроса - создание объявления"""
    pass

# ========== Схема для обновления ==========

class AdvertisementUpdate(BaseModel):
    """Схема для PATCH запроса - все поля опциональны"""
    title: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=100, 
        description="Новый заголовок"
    )
    description: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=1000, 
        description="Новое описание"
    )
    price: Optional[float] = Field(
        None, 
        gt=0, 
        description="Новая цена"
    )
    author: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=100, 
        description="Новый автор"
    )

# ========== Схема для ответа ==========

class AdvertisementResponse(BaseModel):
    """Схема для ответа API - включает id и дату создания"""
    id: int
    title: str
    description: str
    price: float
    author: str
    created_at: str  # Дата в ISO формате строкой
    
    # Pydantic v2 стиль
    model_config = ConfigDict(from_attributes=True)
