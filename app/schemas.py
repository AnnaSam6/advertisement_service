from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime

# ========== Схемы пользователей ==========

class UserCreate(BaseModel):
    """Схема для создания пользователя"""
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    password: str = Field(..., min_length=6, max_length=50, description="Пароль")
    group: str = Field("user", pattern="^(user|admin)$", description="Группа (user или admin)")

class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6, max_length=50)
    group: Optional[str] = Field(None, pattern="^(user|admin)$")

class UserResponse(BaseModel):
    """Схема для ответа с данными пользователя"""
    id: int
    username: str
    group: str
    created_at: str
    
    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    """Схема для логина"""
    username: str
    password: str

class Token(BaseModel):
    """Схема для токена"""
    access_token: str
    token_type: str = "bearer"

# ========== Схемы объявлений ==========

class AdvertisementBase(BaseModel):
    """Базовая схема объявления"""
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=1000)
    price: float = Field(..., gt=0)
    author: str = Field(..., min_length=1, max_length=100)

class AdvertisementCreate(AdvertisementBase):
    """Схема для создания объявления"""
    pass

class AdvertisementUpdate(BaseModel):
    """Схема для обновления объявления"""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    author: Optional[str] = Field(None, min_length=1, max_length=100)

class AdvertisementResponse(BaseModel):
    """Схема для ответа с данными объявления"""
    id: int
    title: str
    description: str
    price: float
    author: str
    user_id: Optional[int] = None
    created_at: str
    
    model_config = ConfigDict(from_attributes=True)
