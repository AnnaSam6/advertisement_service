from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AdvertisementResponse(BaseModel):
    id: int
    title: str
    description: str
    price: float
    author: str
    created_at: datetime

    class Config:
        from_attributes = True

class AdvertisementSearchParams(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    author: Optional[str] = None
