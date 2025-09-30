import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Product, Sale

# Configurar conexão com MySQL (ajuste as credenciais)
DATABASE_URL = "mysql+pymysql://user:password@localhost/venda_certa"
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
holidays = [
    datetime(2021, 12, 25), datetime(2022, 12, 25), datetime(2023, 12, 25),  # Natal
    datetime(2021, 11, 25), datetime(2022, 11, 25), datetime(2023, 11, 25),  # Black Friday
    # Adicionar mais feriados se necessário
]

def is_holiday(date):
    return date in holidays or date.weekday() >= 5  # Sábado/Domingo

def generate_sales():
    session = SessionLocal()
    try:
        # Inserir produtos
        for prod in products_data:
            product = Product(id=prod["id"], name=prod["name"], category=prod["category"])
            session.add(product)
        session.commit()

        # Gerar vendas de 2021-01-01 a 2023-12-31
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
        print("Dados simulados inseridos com sucesso.")
    except Exception as e:
        session.rollback()
        print(f"Erro ao popular banco: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    generate_sales()
