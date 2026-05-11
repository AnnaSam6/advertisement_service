import databases
import sqlalchemy

DATABASE_URL = "sqlite:///./advertisements.db"

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Таблица пользователей
users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("username", sqlalchemy.String(50), unique=True, nullable=False),
    sqlalchemy.Column("password_hash", sqlalchemy.String(128), nullable=False),
    sqlalchemy.Column("group", sqlalchemy.String(10), nullable=False, default="user"),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, nullable=False),
)

# Таблица объявлений (обновленная - добавлен user_id)
advertisements = sqlalchemy.Table(
    "advertisements",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("title", sqlalchemy.String(100), nullable=False),
    sqlalchemy.Column("description", sqlalchemy.String(1000), nullable=False),
    sqlalchemy.Column("price", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("author", sqlalchemy.String(100), nullable=False),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=True),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, nullable=False),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
metadata.create_all(engine)
