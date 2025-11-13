import random
from datetime import datetime, timedelta
import csv

# Produtos simulados
products_data = [
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

# Feriados simulados (datas especiais)
holidays = [
    datetime(2021, 12, 25), datetime(2022, 12, 25), datetime(2023, 12, 25),  # Natal
    datetime(2021, 11, 25), datetime(2022, 11, 25), datetime(2023, 11, 25),  # Black Friday
    datetime(2021, 1, 1), datetime(2022, 1, 1), datetime(2023, 1, 1),  # Ano Novo
    datetime(2021, 2, 14), datetime(2022, 2, 14), datetime(2023, 2, 14),  # Dia dos Namorados
]

def is_holiday(date):
    return date in holidays or date.weekday() >= 5  # Sábado/Domingo

def generate_csv_data(num_rows=3000):
    data = []
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2023, 12, 31)
    current_date = start_date

    while len(data) < num_rows and current_date <= end_date:
        for prod in products_data:
            if len(data) >= num_rows:
                break
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

            data.append({
                'product_id': prod['id'],
                'date': current_date.strftime('%Y-%m-%d'),
                'quantity': quantity,
                'revenue': round(revenue, 2),
                'category': prod['category']
            })
        current_date += timedelta(days=1)

    return data

def save_to_csv(data, filename='docs/dataset_exemplo.csv'):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['product_id', 'date', 'quantity', 'revenue', 'category']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f"Arquivo {filename} gerado com {len(data)} linhas.")

if __name__ == "__main__":
    data = generate_csv_data(1000000)  # Gerar 1 milhão de linhas
    save_to_csv(data, 'docs/dataset_exemplo_1m.csv')
