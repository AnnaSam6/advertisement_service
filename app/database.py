import databases
import sqlalchemy
from sqlalchemy import create_engine, MetaData

DATABASE_URL = "sqlite:///./advertisements.db"

database = databases.Database(DATABASE_URL)
metadata = MetaData()

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

advertisements = sqlalchemy.Table(
    "advertisements",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, index=True),
    sqlalchemy.Column("title", sqlalchemy.String(100), index=True),
    sqlalchemy.Column("description", sqlalchemy.String(1000)),
    sqlalchemy.Column("price", sqlalchemy.Float),
    sqlalchemy.Column("author", sqlalchemy.String(100), index=True),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime),
)

metadata.create_all(engine)
