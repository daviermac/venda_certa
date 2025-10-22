from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import Base, Product, Sale
from typing import List, Optional
from datetime import date

DATABASE_URL = "mysql+pymysql://root:1910@localhost/venda_certa"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Sales API")

@app.get("/products", response_model=List[dict])
def list_products():
    session = SessionLocal()
    try:
        products = session.query(Product).all()
        return [{"id": p.id, "name": p.name, "category": p.category} for p in products]
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
