import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuração da API
SALES_API_URL = "http://localhost:8000"

def get_total_sales():
    """Obtém o total de registros de vendas"""
    try:
        # Usar /sales/history para contar registros
        response = requests.get(f"{SALES_API_URL}/sales/history")
        if response.status_code == 200:
            data = response.json()
            return len(data) if isinstance(data, list) else 0
        else:
            print(f"Erro ao obter total: {response.status_code}")
            return 0
    except Exception as e:
        print(f"Erro de conexão: {e}")
        return 0

def fetch_sales_batch(batch_size=100, offset=0):
    """Busca um lote de vendas"""
    start_time = time.time()
    try:
        # Usar /sales/history sem paginação por enquanto, já que não implementamos limit/offset
        response = requests.get(f"{SALES_API_URL}/sales/history")
        end_time = time.time()
        duration = end_time - start_time

        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else 0
            # Simular paginação retornando apenas o lote solicitado
            start_idx = offset
            end_idx = offset + batch_size
            batch_data = data[start_idx:end_idx] if isinstance(data, list) else []
            return len(batch_data), duration
        else:
            print(f"Erro na requisição: {response.status_code}")
            return 0, duration
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"Erro de conexão: {e}")
        return 0, duration

def stress_test_sequential(num_batches=10, batch_size=100):
    """Teste sequencial de estresse"""
    print(f"\n=== Teste Sequencial: {num_batches} lotes de {batch_size} vendas ===")
    total_sales = 0
    total_time = 0
    times = []

    for i in range(num_batches):
        count, duration = fetch_sales_batch(batch_size, offset=i * batch_size)
        total_sales += count
        total_time += duration
        times.append(duration)
        print(".2f")

    avg_time = total_time / num_batches if num_batches > 0 else 0
    print(f"Total de vendas buscadas: {total_sales}")
    print(".2f")
    print(".2f")
    print(".2f")

def stress_test_concurrent(num_threads=5, num_batches_per_thread=5, batch_size=100):
    """Teste concorrente de estresse"""
    print(f"\n=== Teste Concorrente: {num_threads} threads, {num_batches_per_thread} lotes/thread de {batch_size} vendas ===")

    def worker_thread(thread_id):
        thread_sales = 0
        thread_times = []
        for i in range(num_batches_per_thread):
            offset = (thread_id * num_batches_per_thread + i) * batch_size
            count, duration = fetch_sales_batch(batch_size, offset)
            thread_sales += count
            thread_times.append(duration)
        return thread_sales, thread_times

    start_time = time.time()
    total_sales = 0
    all_times = []

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker_thread, i) for i in range(num_threads)]
        for future in as_completed(futures):
            sales, times = future.result()
            total_sales += sales
            all_times.extend(times)

    end_time = time.time()
    total_duration = end_time - start_time

    avg_time_per_request = sum(all_times) / len(all_times) if all_times else 0
    print(f"Total de vendas buscadas: {total_sales}")
    print(".2f")
    print(".2f")
    print(".2f")
    print(".2f")

if __name__ == "__main__":
    print("=== Teste de Estresse da Sales API ===")

    # Verificar total de vendas
    total_sales = get_total_sales()
    print(f"Total de vendas no banco: {total_sales}")

    # Teste sequencial
    stress_test_sequential(num_batches=10, batch_size=100)

    # Teste concorrente
    stress_test_concurrent(num_threads=5, num_batches_per_thread=5, batch_size=100)

    print("\n=== Teste Concluído ===")
