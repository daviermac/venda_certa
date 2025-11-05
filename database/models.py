from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)

class Sale(Base):
    __tablename__ = 'sales'
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), ForeignKey('products.id'), nullable=False)
    date = Column(Date, nullable=False)
    quantity = Column(Integer, nullable=False)
    revenue = Column(Float, nullable=False)
    product = relationship('Product')

class Forecast(Base):
    __tablename__ = 'forecasts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    scope = Column(String(20), nullable=False)  # 'total', 'category', 'product'
    scope_id = Column(String(50), nullable=True)  # category name or product_id
    date = Column(Date, nullable=False)
    predicted_value = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=True)
    upper_bound = Column(Float, nullable=True)
    model_metadata = Column(Text, nullable=True)  # JSON string with model info

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Trend(Base):
    __tablename__ = 'trends'
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(20), nullable=False)  # 'google', 'amazon'
    product_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    growth_percentage = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Holiday(Base):
    __tablename__ = 'holidays'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    name = Column(String(100), nullable=False)
    is_weekend = Column(Integer, default=0)  # 0=False, 1=True
