from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AdvertisementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=1000)
    price: float = Field(..., gt=0)
    author: str = Field(..., min_length=1, max_length=100)

class AdvertisementUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
