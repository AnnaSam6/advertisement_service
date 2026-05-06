import databases
import sqlalchemy

DATABASE_URL = "sqlite:///./advertisements.db"

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Описание таблицы в БД
advertisements = sqlalchemy.Table(
    "advertisements",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("title", sqlalchemy.String(length=100), nullable=False),
    sqlalchemy.Column("description", sqlalchemy.String(length=1000), nullable=False),
    sqlalchemy.Column("price", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("author", sqlalchemy.String(length=100), nullable=False),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, nullable=False),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
metadata.create_all(engine)
