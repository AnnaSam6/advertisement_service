from pydantic import BaseModel
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
