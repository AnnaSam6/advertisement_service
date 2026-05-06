from fastapi import FastAPI, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime, timezone
import sqlalchemy

# ВНИМАНИЕ: импортируем ТОЛЬКО то, что реально существует!
from .database import database, advertisements
from .schemas import AdvertisementCreate, AdvertisementUpdate, AdvertisementResponse

app = FastAPI(
    title="Advertisement Service API",
    version="1.0.0",
    description="REST API для управления объявлениями купли/продажи"
)

# ========== События жизненного цикла ==========

@app.on_event("startup")
async def startup():
    """Подключение к БД при старте"""
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    """Отключение от БД при завершении"""
    await database.disconnect()

# ========== CRUD Эндпоинты ==========

@app.post(
    "/advertisement",
    response_model=AdvertisementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новое объявление",
    tags=["Объявления"]
)
async def create_advertisement(advertisement: AdvertisementCreate):
    """
    Создание нового объявления.
    
    - **title**: Заголовок (1-100 символов)
    - **description**: Описание (1-1000 символов)  
    - **price**: Цена (> 0)
    - **author**: Автор (1-100 символов)
    """
    current_time = datetime.now(timezone.utc)
    
    query = advertisements.insert().values(
        title=advertisement.title,
        description=advertisement.description,
        price=advertisement.price,
        author=advertisement.author,
        created_at=current_time
    )
    
    last_record_id = await database.execute(query)
    
    # Возвращаем объект с id и датой
    return AdvertisementResponse(
        id=last_record_id,
        title=advertisement.title,
        description=advertisement.description,
        price=advertisement.price,
        author=advertisement.author,
        created_at=current_time.isoformat()
    )


@app.get(
    "/advertisement/{advertisement_id}",
    response_model=AdvertisementResponse,
    summary="Получить объявление по ID",
    tags=["Объявления"]
)
async def get_advertisement(advertisement_id: int):
    """Получение одного объявления по его идентификатору"""
    query = advertisements.select().where(
        advertisements.c.id == advertisement_id
    )
    result = await database.fetch_one(query)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Advertisement with id={advertisement_id} not found"
        )
    
    return AdvertisementResponse(
        id=result["id"],
        title=result["title"],
        description=result["description"],
        price=result["price"],
        author=result["author"],
        created_at=result["created_at"].isoformat()
    )


@app.patch(
    "/advertisement/{advertisement_id}",
    response_model=AdvertisementResponse,
    summary="Обновить объявление",
    tags=["Объявления"]
)
async def update_advertisement(
    advertisement_id: int,
    advertisement_update: AdvertisementUpdate
):
    """
    Частичное обновление объявления.
    Обновляются только переданные поля.
    """
    # Проверка существования
    check_query = advertisements.select().where(
        advertisements.c.id == advertisement_id
    )
    existing = await database.fetch_one(check_query)
    
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Advertisement with id={advertisement_id} not found"
        )
    
    # Получаем только переданные поля
    update_data = advertisement_update.model_dump(exclude_unset=True)
    
    if update_data:
        update_query = advertisements.update().where(
            advertisements.c.id == advertisement_id
        ).values(**update_data)
        await database.execute(update_query)
    
    # Получаем обновлённую запись
    result_query = advertisements.select().where(
        advertisements.c.id == advertisement_id
    )
    updated = await database.fetch_one(result_query)
    
    return AdvertisementResponse(
        id=updated["id"],
        title=updated["title"],
        description=updated["description"],
        price=updated["price"],
        author=updated["author"],
        created_at=updated["created_at"].isoformat()
    )


@app.delete(
    "/advertisement/{advertisement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить объявление",
    tags=["Объявления"]
)
async def delete_advertisement(advertisement_id: int):
    """Удаление объявления по ID"""
    check_query = advertisements.select().where(
        advertisements.c.id == advertisement_id
    )
    existing = await database.fetch_one(check_query)
    
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Advertisement with id={advertisement_id} not found"
        )
    
    delete_query = advertisements.delete().where(
        advertisements.c.id == advertisement_id
    )
    await database.execute(delete_query)
    
    # 204 No Content - тело ответа пустое
    return None


@app.get(
    "/advertisement",
    response_model=List[AdvertisementResponse],
    summary="Поиск объявлений с фильтрацией и пагинацией",
    tags=["Объявления"]
)
async def search_advertisements(
    title: Optional[str] = Query(
        None, 
        description="Частичное совпадение по заголовку"
    ),
    description: Optional[str] = Query(
        None, 
        description="Частичное совпадение по описанию"
    ),
    price_min: Optional[float] = Query(
        None, 
        ge=0, 
        description="Минимальная цена"
    ),
    price_max: Optional[float] = Query(
        None, 
        ge=0, 
        description="Максимальная цена"
    ),
    author: Optional[str] = Query(
        None, 
        description="Частичное совпадение по автору"
    ),
    limit: int = Query(
        10, 
        ge=1, 
        le=100, 
        description="Количество результатов (1-100)"
    ),
    offset: int = Query(
        0, 
        ge=0, 
        description="Смещение для пагинации"
    ),
):
    """
    Поиск объявлений с фильтрацией.
    
    **Особенности:**
    - Все параметры опциональны
    - Текстовый поиск - частичное совпадение (ILIKE)
    - Числовые фильтры - точное сравнение
    - Пагинация через limit/offset
    - Сортировка по дате создания (новые сначала)
    """
    query = advertisements.select()
    conditions = []
    
    # Частичное совпадение для ВСЕХ текстовых полей
    if title:
        conditions.append(advertisements.c.title.ilike(f"%{title}%"))
    
    if description:
        conditions.append(advertisements.c.description.ilike(f"%{description}%"))
    
    if author:
        conditions.append(advertisements.c.author.ilike(f"%{author}%"))
    
    # Точное сравнение для чисел
    if price_min is not None:
        conditions.append(advertisements.c.price >= price_min)
    
    if price_max is not None:
        conditions.append(advertisements.c.price <= price_max)
    
    # Применяем условия
    if conditions:
        query = query.where(sqlalchemy.and_(*conditions))
    
    # Сортировка и пагинация
    query = query.order_by(advertisements.c.created_at.desc())
    query = query.limit(limit).offset(offset)
    
    results = await database.fetch_all(query)
    
    # Преобразуем в список схем
    return [
        AdvertisementResponse(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            price=row["price"],
            author=row["author"],
            created_at=row["created_at"].isoformat()
        )
        for row in results
    ]


@app.get("/", tags=["Служебное"])
async def root():
    """Проверка работоспособности API"""
    return {
        "service": "Advertisement API",
        "status": "running",
        "docs": "/docs",
        "version": "1.0.0"
    }
