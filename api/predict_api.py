from fastapi import FastAPI, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models_mongo import async_db, forecast_helper

forecasts_collection = async_db.forecasts
import httpx
import json
from prophet import Prophet
from datetime import datetime, timedelta
import pandas as pd

app = FastAPI(title="Predict API")

SALES_API_URL = "http://localhost:8000"

async def get_holidays(year: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://brasilapi.com.br/api/feriados/v1/{year}")
        if response.status_code == 200:
            holidays = response.json()
            return [datetime.strptime(h['date'], '%Y-%m-%d').date() for h in holidays]
        return []

async def prepare_data(sales_data, scope, scope_id=None):
    df = pd.DataFrame(sales_data)
    df['date'] = pd.to_datetime(df['date'])

    if scope == 'total':
        df = df.groupby('date')['quantity'].sum().reset_index()
    elif scope == 'category':
        # Para categoria, precisamos fazer join com produtos para obter a categoria
        from database.models_mongo import async_db
        products_collection = async_db.products

        # Buscar produtos da categoria
        product_ids = []
        cursor = products_collection.find({"category": scope_id})
        async for product in cursor:
            product_ids.append(product["id"])

        if product_ids:
            df = df[df['product_id'].isin(product_ids)].groupby('date')['quantity'].sum().reset_index()
        else:
            df = pd.DataFrame(columns=['date', 'quantity'])
    elif scope == 'product':
        df = df[df['product_id'] == scope_id].groupby('date')['quantity'].sum().reset_index()

    df.columns = ['ds', 'y']
    return df

async def fetch_sales_data(scope, scope_id=None, start_date=None, end_date=None):
    params = {}
    if start_date:
        params['start_date'] = start_date.isoformat()
    if end_date:
        params['end_date'] = end_date.isoformat()
    if scope == 'category':
        params['category'] = scope_id
    elif scope == 'product':
        params['product_id'] = scope_id

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SALES_API_URL}/sales/history", params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Erro ao buscar dados de vendas")
        return response.json()

@app.get("/predict")
async def predict(
    scope: str = Query(..., regex="^(total|category|product)$"),
    scope_id: str = Query(None),
    periods: int = Query(30, ge=1, le=365)
):
    if scope in ['category', 'product'] and not scope_id:
        raise HTTPException(status_code=400, detail="scope_id necessário para category ou product")

    # Buscar dados históricos - usar período mais amplo para ter dados suficientes
    end_date = datetime.now().date()
    start_date = datetime(2021, 1, 1).date()  # Dados desde 2021
    sales_data = await fetch_sales_data(scope, scope_id, start_date, end_date)

    if not sales_data:
        raise HTTPException(status_code=404, detail="Nenhum dado histórico encontrado")

    df = await prepare_data(sales_data, scope, scope_id)

    # Adicionar feriados
    holidays = []
    for year in range(start_date.year, end_date.year + 1):
        year_holidays = await get_holidays(year)
        holidays.extend([{'ds': str(h), 'holiday': 'Feriado'} for h in year_holidays])

    # Treinar modelo Prophet
    model = Prophet(holidays=pd.DataFrame(holidays))
    model.fit(df)

    # Fazer previsão
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)

    # Salvar previsões no MongoDB
    try:
        last_historical_date = df['ds'].max()
        for _, row in forecast.iterrows():
            if row['ds'] > last_historical_date:
                pred = {
                    "scope": scope,
                    "scope_id": scope_id,
                    "date": datetime.combine(row['ds'].date(), datetime.min.time()),
                    "predicted_value": row['yhat'],
                    "lower_bound": row['yhat_lower'],
                    "upper_bound": row['yhat_upper'],
                    "model_metadata": json.dumps({'model': 'Prophet'})
                }
                await forecasts_collection.insert_one(pred)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar previsões: {str(e)}")

    # Retornar últimas previsões - usar a última data histórica como referência
    last_historical_date = df['ds'].max()
    predictions = forecast[forecast['ds'] > last_historical_date].to_dict('records')
    return {
        "scope": scope,
        "scope_id": scope_id,
        "predictions": [
            {
                "date": str(p['ds'].date()),
                "predicted_value": p['yhat'],
                "lower_bound": p['yhat_lower'],
                "upper_bound": p['yhat_upper']
            }
            for p in predictions
        ]
    }

@app.get("/recommendation")
async def recommendation(
    scope: str = Query(..., regex="^(total|category|product)$"),
    scope_id: str = Query(None),
    periods: int = Query(30)
):
    # Buscar previsões recentes no MongoDB
    query = {"scope": scope}
    if scope_id:
        query["scope_id"] = scope_id

    cursor = forecasts_collection.find(query).sort("date", -1).limit(periods)
    forecasts = []
    async for forecast in cursor:
        forecasts.append(forecast_helper(forecast))

    if not forecasts:
        # Fallback: calcular baseado em dados históricos se não houver previsões
        print("Nenhuma previsão encontrada, calculando baseado em dados históricos...")
        try:
            end_date = datetime.now().date()
            start_date = datetime(2021, 1, 1).date()
            sales_data = await fetch_sales_data(scope, scope_id, start_date, end_date)

            if sales_data:
                df = await prepare_data(sales_data, scope, scope_id)
                avg_historical = df['y'].mean()
                margin = 1.2  # 20% margem
                recommended_stock = int(avg_historical * margin)

                return {
                    "scope": scope,
                    "scope_id": scope_id,
                    "average_predicted": avg_historical,
                    "recommended_stock": recommended_stock,
                    "source": "historical_data"
                }
        except Exception as e:
            print(f"Erro ao calcular fallback: {e}")

        raise HTTPException(status_code=404, detail="Nenhuma previsão encontrada e falha no cálculo de fallback")

    # Calcular recomendação de estoque (exemplo simples: média prevista * margem)
    total_predicted = sum(f["predicted_value"] for f in forecasts)
    avg_predicted = total_predicted / len(forecasts)
    margin = 1.2  # 20% margem
    recommended_stock = int(avg_predicted * margin)

    return {
        "scope": scope,
        "scope_id": scope_id,
        "average_predicted": avg_predicted,
        "recommended_stock": recommended_stock,
        "source": "forecasts"
    }
