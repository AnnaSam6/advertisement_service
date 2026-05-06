
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Advertisement(Base):
    """ORM модель объявления (опционально)"""
    __tablename__ = "advertisements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=False)
    price = Column(Float, nullable=False)
    author = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False)
