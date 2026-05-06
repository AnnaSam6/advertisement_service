from fastapi import FastAPI, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime, timezone
import sqlalchemy

from .database import database, advertisements
from .models import AdvertisementCreate, AdvertisementUpdate
from .schemas import AdvertisementResponse

app = FastAPI(title="Advertisement Service", version="1.0.0")

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post(
    "/advertisement",
    response_model=AdvertisementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать объявление"
)
async def create_advertisement(advertisement: AdvertisementCreate):
    """
    Создание нового объявления.
    
    - **title**: Заголовок (1-100 символов)
    - **description**: Описание (1-1000 символов)
    - **price**: Цена (больше 0)
    - **author**: Автор (1-100 символов)
    """
    # Создаем дату один раз
    current_time = datetime.now(timezone.utc)
    
    query = advertisements.insert().values(
        title=advertisement.title,
        description=advertisement.description,
        price=advertisement.price,
        author=advertisement.author,
        created_at=current_time
    )
    last_record_id = await database.execute(query)
    
    # Возвращаем с той же датой, что сохранили
    return {
        "id": last_record_id,
        "title": advertisement.title,
        "description": advertisement.description,
        "price": advertisement.price,
        "author": advertisement.author,
        "created_at": current_time.isoformat()
    }

@app.get(
    "/advertisement/{advertisement_id}",
    response_model=AdvertisementResponse,
    summary="Получить объявление по ID"
)
async def get_advertisement(advertisement_id: int):
    """Получение объявления по его идентификатору"""
    query = advertisements.select().where(advertisements.c.id == advertisement_id)
    advertisement = await database.fetch_one(query)
    
    if advertisement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Объявление с id={advertisement_id} не найдено"
        )
    
    # Преобразуем datetime в ISO строку
    result = dict(advertisement)
    result['created_at'] = advertisement['created_at'].isoformat()
    return result

@app.patch(
    "/advertisement/{advertisement_id}",
    response_model=AdvertisementResponse,
    summary="Обновить объявление"
)
async def update_advertisement(
    advertisement_id: int,
    advertisement: AdvertisementUpdate
):
    """Частичное обновление объявления. Можно обновить только нужные поля."""
    # Проверяем существование
    query = advertisements.select().where(advertisements.c.id == advertisement_id)
    existing_ad = await database.fetch_one(query)
    
    if existing_ad is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Объявление с id={advertisement_id} не найдено"
        )
    
    # Обновляем только переданные поля
    update_data = advertisement.model_dump(exclude_unset=True)
    if update_data:
        query = advertisements.update().where(
            advertisements.c.id == advertisement_id
        ).values(**update_data)
        await database.execute(query)
    
    # Возвращаем обновленное объявление
    query = advertisements.select().where(advertisements.c.id == advertisement_id)
    updated_ad = await database.fetch_one(query)
    result = dict(updated_ad)
    result['created_at'] = updated_ad['created_at'].isoformat()
    return result

@app.delete(
    "/advertisement/{advertisement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить объявление"
)
async def delete_advertisement(advertisement_id: int):
    """Удаление объявления по ID"""
    query = advertisements.select().where(advertisements.c.id == advertisement_id)
    advertisement = await database.fetch_one(query)
    
    if advertisement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Объявление с id={advertisement_id} не найдено"
        )
    
    query = advertisements.delete().where(advertisements.c.id == advertisement_id)
    await database.execute(query)

@app.get(
    "/advertisement",
    response_model=List[AdvertisementResponse],
    summary="Поиск объявлений"
)
async def search_advertisements(
    title: Optional[str] = Query(None, description="Поиск по заголовку (частичное совпадение)"),
    description: Optional[str] = Query(None, description="Поиск по описанию (частичное совпадение)"),
    price_min: Optional[float] = Query(None, ge=0, description="Минимальная цена"),
    price_max: Optional[float] = Query(None, ge=0, description="Максимальная цена"),
    author: Optional[str] = Query(None, description="Поиск по автору (частичное совпадение)"),
    limit: int = Query(10, ge=1, le=100, description="Количество результатов на странице"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации")
):
    """
    Поиск объявлений с фильтрацией и пагинацией.
    
    Все параметры опциональны. Поддерживается:
    - Частичный поиск по текстовым полям (title, description, author)
    - Фильтрация по диапазону цен (price_min, price_max)
    - Пагинация через limit и offset
    """
    query = advertisements.select()
    conditions = []
    
    # Все текстовые поиски - ЧАСТИЧНОЕ совпадение (ILIKE)
    if title:
        conditions.append(advertisements.c.title.ilike(f"%{title}%"))
    
    if description:
        conditions.append(advertisements.c.description.ilike(f"%{description}%"))
    
    # Автор теперь тоже с частичным совпадением!
    if author:
        conditions.append(advertisements.c.author.ilike(f"%{author}%"))
    
    # Фильтры по цене
    if price_min is not None:
        conditions.append(advertisements.c.price >= price_min)
    
    if price_max is not None:
        conditions.append(advertisements.c.price <= price_max)
    
    # Применяем все условия
    if conditions:
        query = query.where(sqlalchemy.and_(*conditions))
    
    # Добавляем пагинацию и сортировку
    query = query.order_by(advertisements.c.created_at.desc())
    query = query.limit(limit).offset(offset)
    
    results = await database.fetch_all(query)
    
    # Преобразуем datetime в строки
    return [
        {**dict(row), "created_at": row["created_at"].isoformat()} 
        for row in results
    ]

@app.get("/", summary="Корневой эндпоинт")
async def root():
    """Проверка работоспособности сервиса"""
    return {
        "service": "Advertisement API",
        "version": "1.0.0",
        "docs": "/docs"
    }
