from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId
import os

# Cliente síncrono para operações normais
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://useresenha@vendacerta.jocn1d6.mongodb.net/?appName=vendacerta")
client = MongoClient(MONGODB_URL)
db = client.venda_certa

# Cliente assíncrono para FastAPI
async_client = AsyncIOMotorClient(MONGODB_URL)
async_db = async_client.venda_certa

# Collections
products_collection = db.products
sales_collection = db.sales
forecasts_collection = db.forecasts
users_collection = db.users
trends_collection = db.trends
holidays_collection = db.holidays

# Funções helper para conversão de dados
def product_helper(product) -> dict:
    return {
        "id": product["id"],
        "name": product["name"],
        "category": product["category"],
    }

def sale_helper(sale) -> dict:
    return {
        "id": str(sale["_id"]),
        "product_id": sale["product_id"],
        "date": sale["date"].isoformat() if isinstance(sale["date"], datetime) else sale["date"],
        "quantity": sale["quantity"],
        "revenue": sale["revenue"],
    }

def forecast_helper(forecast) -> dict:
    return {
        "id": str(forecast["_id"]),
        "scope": forecast["scope"],
        "scope_id": forecast.get("scope_id"),
        "date": forecast["date"].isoformat() if isinstance(forecast["date"], datetime) else forecast["date"],
        "predicted_value": forecast["predicted_value"],
        "lower_bound": forecast.get("lower_bound"),
        "upper_bound": forecast.get("upper_bound"),
        "model_metadata": forecast.get("model_metadata"),
    }

def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "password_hash": user["password_hash"],
        "created_at": user["created_at"].isoformat() if isinstance(user["created_at"], datetime) else user["created_at"],
    }

def trend_helper(trend) -> dict:
    return {
        "id": str(trend["_id"]),
        "source": trend["source"],
        "product_name": trend["product_name"],
        "category": trend["category"],
        "growth_percentage": trend["growth_percentage"],
        "created_at": trend["created_at"].isoformat() if isinstance(trend["created_at"], datetime) else trend["created_at"],
    }

def holiday_helper(holiday) -> dict:
    return {
        "id": str(holiday["_id"]),
        "date": holiday["date"].isoformat() if isinstance(holiday["date"], datetime) else holiday["date"],
        "name": holiday["name"],
        "is_weekend": holiday["is_weekend"],
    }
