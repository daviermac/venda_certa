from fastapi import FastAPI, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models_mongo import (
    async_db, db, product_helper, sale_helper,
    user_helper, trend_helper, holiday_helper, async_client
)

# Collections assíncronas
products_collection = async_db.products
sales_collection = async_db.sales
forecasts_collection = async_db.forecasts
users_collection = async_db.users
trends_collection = async_db.trends
holidays_collection = async_db.holidays
from typing import List, Optional
from datetime import date, datetime
import hashlib

app = FastAPI(title="Sales API")

@app.get("/products", response_model=List[dict])
async def list_products():
    products = []
    cursor = products_collection.find()
    async for product in cursor:
        products.append(product_helper(product))
    return products

# Endpoints para usuários
@app.post("/users/login")
async def login_user(username: str, password: str):
    user = await users_collection.find_one({"username": username})
    if user and user["password_hash"] == hashlib.sha256(password.encode()).hexdigest():
        return {"success": True, "message": "Login realizado com sucesso"}
    else:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")

@app.post("/users/register")
async def register_user(username: str, password: str):
    existing_user = await users_collection.find_one({"username": username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Usuário já existe")

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    new_user = {
        "username": username,
        "password_hash": password_hash,
        "created_at": datetime.utcnow()
    }
    await users_collection.insert_one(new_user)
    return {"success": True, "message": "Usuário registrado com sucesso"}

# Endpoints para tendências
@app.get("/trends", response_model=List[dict])
async def get_trends(source: Optional[str] = None):
    query = {}
    if source:
        query["source"] = source
    trends = []
    async for trend in trends_collection.find(query):
        trends.append(trend_helper(trend))
    return trends

# Endpoints para feriados
@app.get("/holidays", response_model=List[dict])
async def get_holidays():
    holidays = []
    async for holiday in holidays_collection.find():
        holidays.append(holiday_helper(holiday))
    return holidays

@app.get("/sales/history", response_model=List[dict])
async def sales_history(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    product_id: Optional[str] = None,
    category: Optional[str] = None
):
    query = {}
    if start_date:
        query["date"] = {"$gte": datetime.combine(start_date, datetime.min.time())}
    if end_date:
        query["date"] = {**query.get("date", {}), "$lte": datetime.combine(end_date, datetime.min.time())}
    if product_id:
        query["product_id"] = product_id

    # Para categoria, precisamos fazer lookup com products
    if category:
        product_ids = []
        async for product in products_collection.find({"category": category}):
            product_ids.append(product["id"])
        if product_ids:
            query["product_id"] = {"$in": product_ids}

    sales = []
    async for sale in sales_collection.find(query):
        sales.append(sale_helper(sale))
    return sales

@app.get("/sales/aggregate", response_model=List[dict])
async def sales_aggregate(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    group_by: str = Query("total", regex="^(total|category|product)$"),
    period: str = Query("daily", regex="^(daily|monthly)$")
):
    # Construir pipeline de agregação do MongoDB
    match_stage = {}
    if start_date:
        match_stage["date"] = {"$gte": datetime.combine(start_date, datetime.min.time())}
    if end_date:
        match_stage["date"] = {**match_stage.get("date", {}), "$lte": datetime.combine(end_date, datetime.min.time())}

    pipeline = []
    if match_stage:
        pipeline.append({"$match": match_stage})

    if group_by == "total":
        if period == "daily":
            pipeline.extend([
                {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}}, "total_quantity": {"$sum": "$quantity"}}},
                {"$sort": {"_id": 1}}
            ])
            results = await sales_collection.aggregate(pipeline).to_list(None)
            return [{"date": r["_id"], "total_quantity": r["total_quantity"]} for r in results]
        elif period == "monthly":
            pipeline.extend([
                {"$group": {"_id": {"$dateToString": {"format": "%Y-%m", "date": "$date"}}, "total_quantity": {"$sum": "$quantity"}}},
                {"$sort": {"_id": 1}}
            ])
            results = await sales_collection.aggregate(pipeline).to_list(None)
            return [{"month": r["_id"], "total_quantity": r["total_quantity"]} for r in results]
    elif group_by == "category":
        # Lookup com products para categoria
        pipeline.extend([
            {"$lookup": {"from": "products", "localField": "product_id", "foreignField": "id", "as": "product"}},
            {"$unwind": "$product"}
        ])
        if period == "daily":
            pipeline.extend([
                {"$group": {"_id": {"date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}}, "category": "$product.category"}, "total_quantity": {"$sum": "$quantity"}}},
                {"$sort": {"_id.date": 1, "_id.category": 1}}
            ])
            results = await sales_collection.aggregate(pipeline).to_list(None)
            return [{"date": r["_id"]["date"], "category": r["_id"]["category"], "total_quantity": r["total_quantity"]} for r in results]
        elif period == "monthly":
            pipeline.extend([
                {"$group": {"_id": {"month": {"$dateToString": {"format": "%Y-%m", "date": "$date"}}, "category": "$product.category"}, "total_quantity": {"$sum": "$quantity"}}},
                {"$sort": {"_id.month": 1, "_id.category": 1}}
            ])
            results = await sales_collection.aggregate(pipeline).to_list(None)
            return [{"month": r["_id"]["month"], "category": r["_id"]["category"], "total_quantity": r["total_quantity"]} for r in results]
    elif group_by == "product":
        if period == "daily":
            pipeline.extend([
                {"$group": {"_id": {"date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}}, "product_id": "$product_id"}, "total_quantity": {"$sum": "$quantity"}}},
                {"$sort": {"_id.date": 1, "_id.product_id": 1}}
            ])
            results = await sales_collection.aggregate(pipeline).to_list(None)
            return [{"date": r["_id"]["date"], "product_id": r["_id"]["product_id"], "total_quantity": r["total_quantity"]} for r in results]
        elif period == "monthly":
            pipeline.extend([
                {"$group": {"_id": {"month": {"$dateToString": {"format": "%Y-%m", "date": "$date"}}, "product_id": "$product_id"}, "total_quantity": {"$sum": "$quantity"}}},
                {"$sort": {"_id.month": 1, "_id.product_id": 1}}
            ])
            results = await sales_collection.aggregate(pipeline).to_list(None)
            return [{"month": r["_id"]["month"], "product_id": r["_id"]["product_id"], "total_quantity": r["total_quantity"]} for r in results]
