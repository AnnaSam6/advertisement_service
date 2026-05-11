from fastapi import FastAPI, HTTPException, Query, Depends, status
from typing import List, Optional
from datetime import datetime, timezone
import sqlalchemy

from .database import database, users, advertisements
from .schemas import (
    UserCreate, UserUpdate, UserResponse, UserLogin, Token,
    AdvertisementCreate, AdvertisementUpdate, AdvertisementResponse
)
from .auth import get_password_hash, verify_password, create_access_token
from .dependencies import get_current_user, get_optional_user

app = FastAPI(
    title="Advertisement Service API",
    version="2.0.0",
    description="REST API с аутентификацией и авторизацией"
)

# ========== События жизненного цикла ==========

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# ========== Аутентификация ==========

@app.post("/login", response_model=Token, tags=["Аутентификация"])
async def login(user_login: UserLogin):
    """
    Аутентификация пользователя.
    
    - **username**: Имя пользователя
    - **password**: Пароль
    - Возвращает JWT токен (действителен 48 часов)
    """
    query = users.select().where(users.c.username == user_login.username)
    user = await database.fetch_one(query)
    
    if user is None or not verify_password(user_login.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["username"]})
    return Token(access_token=access_token)

# ========== Управление пользователями ==========

@app.post("/user", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Пользователи"])
async def create_user(user: UserCreate):
    """
    Создание нового пользователя.
    
    Доступно всем (даже неавторизованным).
    
    - **username**: Имя пользователя (3-50 символов)
    - **password**: Пароль (минимум 6 символов)
    - **group**: Группа (user или admin, по умолчанию user)
    """
    # Проверка уникальности username
    query = users.select().where(users.c.username == user.username)
    existing_user = await database.fetch_one(query)
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    current_time = datetime.now(timezone.utc)
    
    query = users.insert().values(
        username=user.username,
        password_hash=get_password_hash(user.password),
        group=user.group,
        created_at=current_time
    )
    
    user_id = await database.execute(query)
    
    return UserResponse(
        id=user_id,
        username=user.username,
        group=user.group,
        created_at=current_time.isoformat()
    )

@app.get("/user/{user_id}", response_model=UserResponse, tags=["Пользователи"])
async def get_user(user_id: int):
    """
    Получение пользователя по ID.
    
    Доступно всем (даже неавторизованным).
    """
    query = users.select().where(users.c.id == user_id)
    user = await database.fetch_one(query)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={user_id} not found"
        )
    
    return UserResponse(
        id=user["id"],
        username=user["username"],
        group=user["group"],
        created_at=user["created_at"].isoformat()
    )

@app.patch("/user/{user_id}", response_model=UserResponse, tags=["Пользователи"])
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Обновление пользователя.
    
    - Пользователи с группой user могут обновлять только свои данные
    - Администраторы могут обновлять любых пользователей
    """
    # Проверка существования пользователя
    query = users.select().where(users.c.id == user_id)
    existing_user = await database.fetch_one(query)
    
    if existing_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={user_id} not found"
        )
    
    # Проверка прав
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication required"
        )
    
    # Проверка: админ или владелец
    if current_user["group"] != "admin" and current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    
    # Подготовка данных для обновления
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Если обновляется пароль - хешируем его
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    
    # Обычный пользователь не может менять группу
    if "group" in update_data and current_user["group"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can change user group"
        )
    
    if update_data:
        query = users.update().where(users.c.id == user_id).values(**update_data)
        await database.execute(query)
    
    # Получение обновленных данных
    query = users.select().where(users.c.id == user_id)
    updated_user = await database.fetch_one(query)
    
    return UserResponse(
        id=updated_user["id"],
        username=updated_user["username"],
        group=updated_user["group"],
        created_at=updated_user["created_at"].isoformat()
    )

@app.delete("/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Пользователи"])
async def delete_user(
    user_id: int,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Удаление пользователя.
    
    - Пользователи с группой user могут удалить только себя
    - Администраторы могут удалить любого пользователя
    """
    # Проверка существования
    query = users.select().where(users.c.id == user_id)
    existing_user = await database.fetch_one(query)
    
    if existing_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={user_id} not found"
        )
    
    # Проверка прав
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication required"
        )
    
    if current_user["group"] != "admin" and current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own account"
        )
    
    query = users.delete().where(users.c.id == user_id)
    await database.execute(query)
    
    return None

# ========== Объявления (с авторизацией) ==========

@app.post("/advertisement", response_model=AdvertisementResponse, status_code=status.HTTP_201_CREATED, tags=["Объявления"])
async def create_advertisement(
    advertisement: AdvertisementCreate,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Создание объявления.
    
    - Только для авторизованных пользователей (группы user или admin)
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication required to create advertisements"
        )
    
    current_time = datetime.now(timezone.utc)
    
    query = advertisements.insert().values(
        title=advertisement.title,
        description=advertisement.description,
        price=advertisement.price,
        author=advertisement.author,
        user_id=current_user["id"],
        created_at=current_time
    )
    
    ad_id = await database.execute(query)
    
    return AdvertisementResponse(
        id=ad_id,
        title=advertisement.title,
        description=advertisement.description,
        price=advertisement.price,
        author=advertisement.author,
        user_id=current_user["id"],
        created_at=current_time.isoformat()
    )

@app.get("/advertisement/{advertisement_id}", response_model=AdvertisementResponse, tags=["Объявления"])
async def get_advertisement(advertisement_id: int):
    """
    Получение объявления по ID.
    
    Доступно всем.
    """
    query = advertisements.select().where(advertisements.c.id == advertisement_id)
    ad = await database.fetch_one(query)
    
    if ad is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Advertisement with id={advertisement_id} not found"
        )
    
    return AdvertisementResponse(
        id=ad["id"],
        title=ad["title"],
        description=ad["description"],
        price=ad["price"],
        author=ad["author"],
        user_id=ad["user_id"],
        created_at=ad["created_at"].isoformat()
    )

@app.patch("/advertisement/{advertisement_id}", response_model=AdvertisementResponse, tags=["Объявления"])
async def update_advertisement(
    advertisement_id: int,
    advertisement_update: AdvertisementUpdate,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Обновление объявления.
    
    - Пользователи могут обновлять только свои объявления
    - Администраторы могут обновлять любые объявления
    """
    # Проверка существования
    query = advertisements.select().where(advertisements.c.id == advertisement_id)
    existing_ad = await database.fetch_one(query)
    
    if existing_ad is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Advertisement with id={advertisement_id} not found"
        )
    
    # Проверка прав
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication required"
        )
    
    if current_user["group"] != "admin" and current_user["id"] != existing_ad["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own advertisements"
        )
    
    update_data = advertisement_update.model_dump(exclude_unset=True)
    
    if update_data:
        query = advertisements.update().where(
            advertisements.c.id == advertisement_id
        ).values(**update_data)
        await database.execute(query)
    
    query = advertisements.select().where(advertisements.c.id == advertisement_id)
    updated_ad = await database.fetch_one(query)
    
    return AdvertisementResponse(
        id=updated_ad["id"],
        title=updated_ad["title"],
        description=updated_ad["description"],
        price=updated_ad["price"],
        author=updated_ad["author"],
        user_id=updated_ad["user_id"],
        created_at=updated_ad["created_at"].isoformat()
    )

@app.delete("/advertisement/{advertisement_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Объявления"])
async def delete_advertisement(
    advertisement_id: int,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Удаление объявления.
    
    - Пользователи могут удалять только свои объявления
    - Администраторы могут удалять любые объявления
    """
    query = advertisements.select().where(advertisements.c.id == advertisement_id)
    existing_ad = await database.fetch_one(query)
    
    if existing_ad is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Advertisement with id={advertisement_id} not found"
        )
    
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication required"
        )
    
    if current_user["group"] != "admin" and current_user["id"] != existing_ad["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own advertisements"
        )
    
    query = advertisements.delete().where(advertisements.c.id == advertisement_id)
    await database.execute(query)
    
    return None

@app.get("/advertisement", response_model=List[AdvertisementResponse], tags=["Объявления"])
async def search_advertisements(
    title: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    price_min: Optional[float] = Query(None, ge=0),
    price_max: Optional[float] = Query(None, ge=0),
    author: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Поиск объявлений с фильтрацией и пагинацией.
    
    Доступно всем.
    """
    query = advertisements.select()
    conditions = []
    
    if title:
        conditions.append(advertisements.c.title.ilike(f"%{title}%"))
    if description:
        conditions.append(advertisements.c.description.ilike(f"%{description}%"))
    if author:
        conditions.append(advertisements.c.author.ilike(f"%{author}%"))
    if price_min is not None:
        conditions.append(advertisements.c.price >= price_min)
    if price_max is not None:
        conditions.append(advertisements.c.price <= price_max)
    
    if conditions:
        query = query.where(sqlalchemy.and_(*conditions))
    
    query = query.order_by(advertisements.c.created_at.desc())
    query = query.limit(limit).offset(offset)
    
    results = await database.fetch_all(query)
    
    return [
        AdvertisementResponse(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            price=row["price"],
            author=row["author"],
            user_id=row["user_id"],
            created_at=row["created_at"].isoformat()
        )
        for row in results
    ]

@app.get("/", tags=["Служебное"])
async def root():
    return {
        "service": "Advertisement API",
        "version": "2.0.0",
        "docs": "/docs"
    }
