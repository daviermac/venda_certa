from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Forecast
import httpx
import json
from prophet import Prophet
from datetime import datetime, timedelta
import pandas as pd

DATABASE_URL = "mysql+pymysql://davi:1910@localhost/venda_certa"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Predict API")

SALES_API_URL = "http://localhost:8000"  

async def get_holidays(year: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://brasilapi.com.br/api/feriados/v1/{year}")
        if response.status_code == 200:
            holidays = response.json()
            return [datetime.strptime(h['date'], '%Y-%m-%d').date() for h in holidays]
        return []

def prepare_data(sales_data, scope, scope_id=None):
    df = pd.DataFrame(sales_data)
    df['date'] = pd.to_datetime(df['date'])
    if scope == 'total':
        df = df.groupby('date')['quantity'].sum().reset_index()
    elif scope == 'category':
        df = df[df['category'] == scope_id].groupby('date')['quantity'].sum().reset_index()
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

    # Buscar dados históricos
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365*2)  # Últimos 2 anos
    sales_data = await fetch_sales_data(scope, scope_id, start_date, end_date)

    if not sales_data:
        raise HTTPException(status_code=404, detail="Nenhum dado histórico encontrado")

    df = prepare_data(sales_data, scope, scope_id)

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

    # Salvar previsões no banco
    session = SessionLocal()
    try:
        for _, row in forecast.iterrows():
            if row['ds'].date() > end_date:
                pred = Forecast(
                    scope=scope,
                    scope_id=scope_id,
                    date=row['ds'].date(),
                    predicted_value=row['yhat'],
                    lower_bound=row['yhat_lower'],
                    upper_bound=row['yhat_upper'],
                    model_metadata=json.dumps({'model': 'Prophet'})
                )
                session.add(pred)
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao salvar previsões: {str(e)}")
    finally:
        session.close()

    # Retornar últimas previsões
    predictions = forecast[forecast['ds'] > pd.to_datetime(end_date)].to_dict('records')
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
    # Buscar previsões recentes
    session = SessionLocal()
    try:
        query = session.query(Forecast).filter(Forecast.scope == scope)
        if scope_id:
            query = query.filter(Forecast.scope_id == scope_id)
        forecasts = query.order_by(Forecast.date.desc()).limit(periods).all()

        if not forecasts:
            raise HTTPException(status_code=404, detail="Nenhuma previsão encontrada")

        # Calcular recomendação de estoque (exemplo simples: média prevista * margem)
        total_predicted = sum(f.predicted_value for f in forecasts)
        avg_predicted = total_predicted / len(forecasts)
        margin = 1.2  # 20% margem
        recommended_stock = int(avg_predicted * margin)

        return {
            "scope": scope,
            "scope_id": scope_id,
            "average_predicted": avg_predicted,
            "recommended_stock": recommended_stock
        }
    finally:
        session.close()
