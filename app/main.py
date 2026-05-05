from fastapi import FastAPI, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime
import sqlalchemy

from .database import database, advertisements
from .models import AdvertisementCreate, AdvertisementUpdate
from .schemas import AdvertisementResponse

app = FastAPI(title="Advertisement Service")

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/advertisement", response_model=AdvertisementResponse, status_code=status.HTTP_201_CREATED)
async def create_advertisement(advertisement: AdvertisementCreate):
    # Исправлено: вычисляем время один раз
    current_time = datetime.utcnow()
    
    query = advertisements.insert().values(
        title=advertisement.title,
        description=advertisement.description,
        price=advertisement.price,
        author=advertisement.author,
        created_at=current_time
    )
    last_record_id = await database.execute(query)
    
    return {
        "id": last_record_id,
        "title": advertisement.title,
        "description": advertisement.description,
        "price": advertisement.price,
        "author": advertisement.author,
        "created_at": current_time
    }

@app.get("/advertisement/{advertisement_id}", response_model=AdvertisementResponse)
async def get_advertisement(advertisement_id: int):
    query = advertisements.select().where(advertisements.c.id == advertisement_id)
    advertisement = await database.fetch_one(query)
    
    if advertisement is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    
    return advertisement

@app.patch("/advertisement/{advertisement_id}", response_model=AdvertisementResponse)
async def update_advertisement(advertisement_id: int, advertisement_update: AdvertisementUpdate):
    # Проверяем существование объявления
    query = advertisements.select().where(advertisements.c.id == advertisement_id)
    existing_ad = await database.fetch_one(query)
    
    if existing_ad is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    
    # Обновляем только переданные поля
    update_data = advertisement_update.dict(exclude_unset=True)
    if update_data:
        query = advertisements.update().where(
            advertisements.c.id == advertisement_id
        ).values(**update_data)
        await database.execute(query)
    
    # Возвращаем обновленное объявление
    query = advertisements.select().where(advertisements.c.id == advertisement_id)
    updated_ad = await database.fetch_one(query)
    return updated_ad

@app.delete("/advertisement/{advertisement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_advertisement(advertisement_id: int):
    query = advertisements.select().where(advertisements.c.id == advertisement_id)
    advertisement = await database.fetch_one(query)
    
    if advertisement is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    
    query = advertisements.delete().where(advertisements.c.id == advertisement_id)
    await database.execute(query)

@app.get("/advertisement", response_model=List[AdvertisementResponse])
async def search_advertisements(
    title: Optional[str] = Query(None, description="Search by title (partial match)"),
    description: Optional[str] = Query(None, description="Search by description (partial match)"),
    price_min: Optional[float] = Query(None, description="Minimum price"),
    price_max: Optional[float] = Query(None, description="Maximum price"),
    author: Optional[str] = Query(None, description="Search by author (exact match)"),
    limit: int = Query(10, ge=1, le=100, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    query = advertisements.select()
    
    # Добавляем условия фильтрации
    conditions = []
    
    if title:
        conditions.append(advertisements.c.title.ilike(f"%{title}%"))
    if description:
        conditions.append(advertisements.c.description.ilike(f"%{description}%"))
    if price_min is not None:
        conditions.append(advertisements.c.price >= price_min)
    if price_max is not None:
        conditions.append(advertisements.c.price <= price_max)
    if author:
        # Исправлено: точное совпадение для автора
        conditions.append(advertisements.c.author == author)
    
    if conditions:
        query = query.where(sqlalchemy.and_(*conditions))
    
    # Добавляем пагинацию
    query = query.limit(limit).offset(offset)
    
    results = await database.fetch_all(query)
    return results
