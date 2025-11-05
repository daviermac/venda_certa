import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base, Product, Sale, User, Trend, Holiday
import hashlib

# Configurar conexão com MySQL usuario e senha
DATABASE_URL = "mysql+pymysql://root:1910@localhost/venda_certa"

temp_engine = create_engine("mysql+pymysql://root:1910@localhost")
with temp_engine.connect() as conn:
    conn.execute(text("CREATE DATABASE IF NOT EXISTS venda_certa"))
    conn.commit()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar tabelas
Base.metadata.create_all(bind=engine)

# Produtos simulados
products_data = [
    {"id": "P1", "name": "Smartphone", "category": "Eletrônicos"},
    {"id": "P2", "name": "Notebook", "category": "Eletrônicos"},
    {"id": "P3", "name": "Camiseta", "category": "Roupas"},
    {"id": "P4", "name": "Calça Jeans", "category": "Roupas"},
    {"id": "P5", "name": "Livro", "category": "Livros"},
    {"id": "P6", "name": "Cadeira", "category": "Móveis"},
]

# Feriados simulados (datas especiais)
holidays_data = [
    {"date": datetime(2021, 12, 25), "name": "Natal"},
    {"date": datetime(2022, 12, 25), "name": "Natal"},
    {"date": datetime(2023, 12, 25), "name": "Natal"},
    {"date": datetime(2021, 11, 25), "name": "Black Friday"},
    {"date": datetime(2022, 11, 25), "name": "Black Friday"},
    {"date": datetime(2023, 11, 25), "name": "Black Friday"},
    {"date": datetime(2021, 1, 1), "name": "Ano Novo"},
    {"date": datetime(2022, 1, 1), "name": "Ano Novo"},
    {"date": datetime(2023, 1, 1), "name": "Ano Novo"},
    {"date": datetime(2021, 2, 14), "name": "Dia dos Namorados"},
    {"date": datetime(2022, 2, 14), "name": "Dia dos Namorados"},
    {"date": datetime(2023, 2, 14), "name": "Dia dos Namorados"},
]

# Usuários iniciais
users_data = [
    {"username": "davi", "password": "1910"},
]

# Tendências simuladas
trends_data = [
    {"source": "amazon", "product_name": "Smartwatch", "category": "Tecnologia", "growth": "+45%"},
    {"source": "amazon", "product_name": "Fones Bluetooth", "category": "Eletrônicos", "growth": "+37%"},
    {"source": "amazon", "product_name": "Tênis esportivo", "category": "Moda", "growth": "+28%"},
    {"source": "amazon", "product_name": "Air Fryer", "category": "Casa", "growth": "+32%"},
    {"source": "amazon", "product_name": "Notebook Gamer", "category": "Informática", "growth": "+25%"},
]

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_holiday(date):
    holiday_dates = [h["date"] for h in holidays_data]
    return date in holiday_dates or date.weekday() >= 5  # Sábado/Domingo

def populate_database():
    session = SessionLocal()
    try:
        # Inserir produtos
        existing_products = session.query(Product.id).all()
        existing_ids = {p.id for p in existing_products}
        for prod in products_data:
            if prod["id"] not in existing_ids:
                product = Product(id=prod["id"], name=prod["name"], category=prod["category"])
                session.add(product)
        session.commit()

        # Inserir usuários
        existing_users = session.query(User.username).all()
        existing_usernames = {u.username for u in existing_users}
        for user_data in users_data:
            if user_data["username"] not in existing_usernames:
                user = User(
                    username=user_data["username"],
                    password_hash=hash_password(user_data["password"])
                )
                session.add(user)
        session.commit()

        # Inserir feriados
        existing_holidays = session.query(Holiday.date).all()
        existing_dates = {h.date for h in existing_holidays}
        for holiday_data in holidays_data:
            if holiday_data["date"].date() not in existing_dates:
                holiday = Holiday(
                    date=holiday_data["date"].date(),
                    name=holiday_data["name"],
                    is_weekend=0
                )
                session.add(holiday)
        session.commit()

        # Inserir tendências
        session.query(Trend).delete()  # Limpar tendências antigas
        for trend_data in trends_data:
            trend = Trend(
                source=trend_data["source"],
                product_name=trend_data["product_name"],
                category=trend_data["category"],
                growth_percentage=trend_data["growth"]
            )
            session.add(trend)
        session.commit()

        # Gerar vendas de 2021-01-01 a 2023-12-31
        existing_sales_count = session.query(Sale).count()
        if existing_sales_count == 0:
            start_date = datetime(2021, 1, 1)
            end_date = datetime(2023, 12, 31)
            current_date = start_date

            while current_date <= end_date:
                for prod in products_data:
                    # Base quantity
                    base_qty = random.randint(1, 20)
                    # Seasonal multiplier: higher in Dec, Nov
                    month = current_date.month
                    if month in [11, 12]:
                        multiplier = random.uniform(1.5, 3.0)
                    elif month in [6, 7]:  # Summer
                        multiplier = random.uniform(1.2, 2.0)
                    else:
                        multiplier = random.uniform(0.5, 1.5)
                    # Holiday boost
                    if is_holiday(current_date):
                        multiplier *= random.uniform(1.5, 2.5)
                    quantity = int(base_qty * multiplier)
                    if quantity < 1:
                        quantity = 1
                    # Revenue: assume price per unit
                    price_per_unit = random.uniform(50, 500)
                    revenue = quantity * price_per_unit

                    sale = Sale(product_id=prod["id"], date=current_date.date(), quantity=quantity, revenue=round(revenue, 2))
                    session.add(sale)
                current_date += timedelta(days=1)
            session.commit()

        print("Banco populado com sucesso!")
    except Exception as e:
        session.rollback()
        print(f"Erro ao popular banco: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    populate_database()
