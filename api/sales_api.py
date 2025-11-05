from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import Base, Product, Sale, User, Trend, Holiday
from typing import List, Optional
from datetime import date
import hashlib

DATABASE_URL = "mysql+pymysql://root:1910@localhost/venda_certa"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar tabelas se não existirem
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sales API")

@app.get("/products", response_model=List[dict])
def list_products():
    session = SessionLocal()
    try:
        products = session.query(Product).all()
        return [{"id": p.id, "name": p.name, "category": p.category} for p in products]
    finally:
        session.close()

# Endpoints para usuários
@app.post("/users/login")
def login_user(username: str, password: str):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.username == username).first()
        if user and user.password_hash == hashlib.sha256(password.encode()).hexdigest():
            return {"success": True, "message": "Login realizado com sucesso"}
        else:
            raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")
    finally:
        session.close()

@app.post("/users/register")
def register_user(username: str, password: str):
    session = SessionLocal()
    try:
        existing_user = session.query(User).filter(User.username == username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Usuário já existe")

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        new_user = User(username=username, password_hash=password_hash)
        session.add(new_user)
        session.commit()
        return {"success": True, "message": "Usuário registrado com sucesso"}
    finally:
        session.close()

# Endpoints para tendências
@app.get("/trends", response_model=List[dict])
def get_trends(source: Optional[str] = None):
    session = SessionLocal()
    try:
        query = session.query(Trend)
        if source:
            query = query.filter(Trend.source == source)
        trends = query.all()
        return [
            {
                "id": t.id,
                "source": t.source,
                "product_name": t.product_name,
                "category": t.category,
                "growth_percentage": t.growth_percentage,
                "created_at": t.created_at.isoformat()
            }
            for t in trends
        ]
    finally:
        session.close()

# Endpoints para feriados
@app.get("/holidays", response_model=List[dict])
def get_holidays():
    session = SessionLocal()
    try:
        holidays = session.query(Holiday).all()
        return [
            {
                "id": h.id,
                "date": h.date.isoformat(),
                "name": h.name,
                "is_weekend": h.is_weekend
            }
            for h in holidays
        ]
    finally:
        session.close()

@app.get("/sales/history", response_model=List[dict])
def sales_history(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    product_id: Optional[str] = None,
    category: Optional[str] = None
):
    session = SessionLocal()
    try:
        query = session.query(Sale).join(Product)
        if start_date:
            query = query.filter(Sale.date >= start_date)
        if end_date:
            query = query.filter(Sale.date <= end_date)
        if product_id:
            query = query.filter(Sale.product_id == product_id)
        if category:
            query = query.filter(Product.category == category)
        sales = query.all()
        return [
            {
                "id": s.id,
                "product_id": s.product_id,
                "date": s.date.isoformat(),
                "quantity": s.quantity,
                "revenue": s.revenue
            }
            for s in sales
        ]
    finally:
        session.close()

@app.get("/sales/aggregate", response_model=List[dict])
def sales_aggregate(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    group_by: str = Query("total", regex="^(total|category|product)$"),
    period: str = Query("daily", regex="^(daily|monthly)$")
):
    session = SessionLocal()
    try:
        query = session.query()
        if group_by == "total":
            if period == "daily":
                query = session.query(Sale.date, func.sum(Sale.quantity).label("total_quantity"))
                if start_date:
                    query = query.filter(Sale.date >= start_date)
                if end_date:
                    query = query.filter(Sale.date <= end_date)
                query = query.group_by(Sale.date).order_by(Sale.date)
                results = query.all()
                return [{"date": r.date.isoformat(), "total_quantity": r.total_quantity} for r in results]
            elif period == "monthly":
                query = session.query(func.strftime("%Y-%m", Sale.date).label("month"), func.sum(Sale.quantity).label("total_quantity"))
                if start_date:
                    query = query.filter(Sale.date >= start_date)
                if end_date:
                    query = query.filter(Sale.date <= end_date)
                query = query.group_by("month").order_by("month")
                results = query.all()
                return [{"month": r.month, "total_quantity": r.total_quantity} for r in results]
        elif group_by == "category":
            if period == "daily":
                query = session.query(Sale.date, Product.category, func.sum(Sale.quantity).label("total_quantity")).join(Product)
                if start_date:
                    query = query.filter(Sale.date >= start_date)
                if end_date:
                    query = query.filter(Sale.date <= end_date)
                query = query.group_by(Sale.date, Product.category).order_by(Sale.date, Product.category)
                results = query.all()
                return [{"date": r.date.isoformat(), "category": r.category, "total_quantity": r.total_quantity} for r in results]
            elif period == "monthly":
                query = session.query(func.strftime("%Y-%m", Sale.date).label("month"), Product.category, func.sum(Sale.quantity).label("total_quantity")).join(Product)
                if start_date:
                    query = query.filter(Sale.date >= start_date)
                if end_date:
                    query = query.filter(Sale.date <= end_date)
                query = query.group_by("month", Product.category).order_by("month", Product.category)
                results = query.all()
                return [{"month": r.month, "category": r.category, "total_quantity": r.total_quantity} for r in results]
        elif group_by == "product":
            if period == "daily":
                query = session.query(Sale.date, Sale.product_id, func.sum(Sale.quantity).label("total_quantity")).join(Product)
                if start_date:
                    query = query.filter(Sale.date >= start_date)
                if end_date:
                    query = query.filter(Sale.date <= end_date)
                query = query.group_by(Sale.date, Sale.product_id).order_by(Sale.date, Sale.product_id)
                results = query.all()
                return [{"date": r.date.isoformat(), "product_id": r.product_id, "total_quantity": r.total_quantity} for r in results]
            elif period == "monthly":
                query = session.query(func.strftime("%Y-%m", Sale.date).label("month"), Sale.product_id, func.sum(Sale.quantity).label("total_quantity")).join(Product)
                if start_date:
                    query = query.filter(Sale.date >= start_date)
                if end_date:
                    query = query.filter(Sale.date <= end_date)
                query = query.group_by("month", Sale.product_id).order_by("month", Sale.product_id)
                results = query.all()
                return [{"month": r.month, "product_id": r.product_id, "total_quantity": r.total_quantity} for r in results]
    finally:
        session.close()
