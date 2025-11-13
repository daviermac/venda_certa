import pandas as pd
from database.models_mongo import (
    db, products_collection, sales_collection,
    users_collection, trends_collection, holidays_collection
)
from datetime import datetime, timedelta
import hashlib

def populate_products():
    """Popula a coleção de produtos"""
    products = [
        {"id": "P1", "name": "Smartphone", "category": "Eletrônicos"},
        {"id": "P2", "name": "Notebook", "category": "Eletrônicos"},
        {"id": "P3", "name": "Camiseta", "category": "Roupas"},
        {"id": "P4", "name": "Calça Jeans", "category": "Roupas"},
        {"id": "P5", "name": "Livro", "category": "Livros"},
        {"id": "P6", "name": "Cadeira", "category": "Móveis"},
        {"id": "P7", "name": "Tablet", "category": "Eletrônicos"},
        {"id": "P8", "name": "Vestido", "category": "Roupas"},
        {"id": "P9", "name": "Revista", "category": "Livros"},
        {"id": "P10", "name": "Mesa", "category": "Móveis"},
    ]

    # Limpar coleção existente
    products_collection.delete_many({})

    # Inserir produtos
    products_collection.insert_many(products)
    print(f"Inseridos {len(products)} produtos")

def populate_sales_from_csv(csv_file='docs/dataset_exemplo_1m.csv'):
    """Popula vendas a partir do CSV gerado"""
    try:
        df = pd.read_csv(csv_file)
        print(f"Lendo {len(df)} linhas do CSV...")

        # Converter datas
        df['date'] = pd.to_datetime(df['date'])

        # Limpar coleção existente
        sales_collection.delete_many({})

        # Preparar dados para inserção
        sales_data = []
        for _, row in df.iterrows():
            sale = {
                "product_id": row['product_id'],
                "date": datetime.combine(row['date'].date(), datetime.min.time()),
                "quantity": int(row['quantity']),
                "revenue": float(row['revenue'])
            }
            sales_data.append(sale)

        # Inserir em lotes para melhor performance
        batch_size = 1000
        for i in range(0, len(sales_data), batch_size):
            batch = sales_data[i:i+batch_size]
            sales_collection.insert_many(batch)
            print(f"Inserido lote {i//batch_size + 1} de {len(batch)} vendas")

        print(f"Total de vendas inseridas: {len(sales_data)}")

    except FileNotFoundError:
        print(f"Arquivo {csv_file} não encontrado. Execute generate_csv.py primeiro.")
    except Exception as e:
        print(f"Erro ao popular vendas: {e}")

def populate_users():
    """Popula usuários de exemplo"""
    users = [
        {
            "username": "admin",
            "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
            "created_at": datetime.utcnow()
        },
        {
            "username": "user1",
            "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
            "created_at": datetime.utcnow()
        }
    ]

    # Limpar coleção existente
    users_collection.delete_many({})

    # Inserir usuários
    users_collection.insert_many(users)
    print(f"Inseridos {len(users)} usuários")

def populate_trends():
    """Popula tendências de exemplo"""
    trends = [
        {
            "source": "amazon",
            "product_name": "Smartwatch",
            "category": "Tecnologia",
            "growth_percentage": 45.0,
            "created_at": datetime.utcnow()
        },
        {
            "source": "amazon",
            "product_name": "Fones Bluetooth",
            "category": "Eletrônicos",
            "growth_percentage": 37.0,
            "created_at": datetime.utcnow()
        },
        {
            "source": "amazon",
            "product_name": "Tênis esportivo",
            "category": "Moda",
            "growth_percentage": 28.0,
            "created_at": datetime.utcnow()
        },
        {
            "source": "amazon",
            "product_name": "Air Fryer",
            "category": "Casa",
            "growth_percentage": 32.0,
            "created_at": datetime.utcnow()
        },
        {
            "source": "amazon",
            "product_name": "Notebook Gamer",
            "category": "Informática",
            "growth_percentage": 25.0,
            "created_at": datetime.utcnow()
        }
    ]

    # Limpar coleção existente
    trends_collection.delete_many({})

    # Inserir tendências
    trends_collection.insert_many(trends)
    print(f"Inseridas {len(trends)} tendências")

def populate_holidays():
    """Popula feriados brasileiros"""
    holidays = [
        {"date": datetime(2021, 12, 25), "name": "Natal", "is_weekend": False},
        {"date": datetime(2022, 12, 25), "name": "Natal", "is_weekend": False},
        {"date": datetime(2023, 12, 25), "name": "Natal", "is_weekend": False},
        {"date": datetime(2021, 11, 25), "name": "Black Friday", "is_weekend": False},
        {"date": datetime(2022, 11, 25), "name": "Black Friday", "is_weekend": False},
        {"date": datetime(2023, 11, 25), "name": "Black Friday", "is_weekend": False},
        {"date": datetime(2021, 1, 1), "name": "Ano Novo", "is_weekend": False},
        {"date": datetime(2022, 1, 1), "name": "Ano Novo", "is_weekend": False},
        {"date": datetime(2023, 1, 1), "name": "Ano Novo", "is_weekend": False},
        {"date": datetime(2021, 2, 14), "name": "Dia dos Namorados", "is_weekend": False},
        {"date": datetime(2022, 2, 14), "name": "Dia dos Namorados", "is_weekend": False},
        {"date": datetime(2023, 2, 14), "name": "Dia dos Namorados", "is_weekend": False},
    ]

    # Adicionar fins de semana
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2023, 12, 31)
    current_date = start_date

    while current_date <= end_date:
        if current_date.weekday() >= 5:  # Sábado ou Domingo
            holidays.append({
                "date": current_date,
                "name": "Fim de Semana",
                "is_weekend": True
            })
        current_date += timedelta(days=1)

    # Limpar coleção existente
    holidays_collection.delete_many({})

    # Inserir feriados
    holidays_collection.insert_many(holidays)
    print(f"Inseridos {len(holidays)} feriados/fins de semana")

if __name__ == "__main__":
    print("Iniciando população do banco MongoDB...")

    try:
        populate_products()
        populate_sales_from_csv()
        populate_users()
        populate_trends()
        populate_holidays()

        print("População concluída com sucesso!")

    except Exception as e:
        print(f"Erro durante a população: {e}")
