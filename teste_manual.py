import requests
import time

# Configuração da API
SALES_API_URL = "http://localhost:8000"

def teste_manual():
    """Teste manual simples para demonstração"""
    print("=== TESTE MANUAL DE PERFORMANCE DA SALES API ===\n")

    # 1. Verificar total de vendas
    print("1. Verificando total de vendas no banco...")
    start_time = time.time()
    try:
        response = requests.get(f"{SALES_API_URL}/sales/history")
        end_time = time.time()
        if response.status_code == 200:
            data = response.json()
            total_vendas = len(data) if isinstance(data, list) else 0
            tempo_total = end_time - start_time
            print(f"   ✓ Total de vendas: {total_vendas}")
            print(".2f")
        else:
            print(f"   ✗ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Erro de conexão: {e}")

    print("\n2. Teste sequencial de diferentes volumes...")

    # Teste com diferentes quantidades de requisições (reduzido para não travar)
    volumes = [10, 50, 100]

    for num_requests in volumes:
        print(f"\n   Testando {num_requests} requisições:")
        tempos = []
        start_batch = time.time()

        # Executa as requisições
        for i in range(num_requests):
            start_time = time.time()
            try:
                response = requests.get(f"{SALES_API_URL}/sales/history")
                end_time = time.time()
                if response.status_code == 200:
                    tempo = end_time - start_time
                    tempos.append(tempo)
                else:
                    print(f"     ✗ Requisição {i+1}: Erro {response.status_code}")
                    break
            except Exception as e:
                end_time = time.time()
                tempo = end_time - start_time
                tempos.append(tempo)

        end_batch = time.time()
        tempo_total_batch = end_batch - start_batch

        if tempos:
            tempo_medio = sum(tempos) / len(tempos)
            tempo_min = min(tempos)
            tempo_max = max(tempos)
            throughput = num_requests / tempo_total_batch if tempo_total_batch > 0 else 0

            print(f"     Tempo total do lote: {tempo_total_batch:.2f} segundos")
            print(f"     Tempo médio por requisição: {tempo_medio:.2f} segundos")
            print(f"     Tempo mínimo: {tempo_min:.2f} segundos")
            print(f"     Tempo máximo: {tempo_max:.2f} segundos")
            print(f"     Throughput: {throughput:.1f} req/segundo")
            print(f"     Tempo total estimado: {tempo_total_batch:.2f} segundos")

    print("\n3. Teste de agregação por categoria...")
    start_time = time.time()
    try:
        response = requests.get(f"{SALES_API_URL}/sales/aggregate", params={"group_by": "category", "period": "daily"})
        end_time = time.time()
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else 0
            tempo = end_time - start_time
            print(f"   ✓ Agregação por categoria: {count} registros")
            print(".2f")
        else:
            print(f"   ✗ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Erro de conexão: {e}")

    print("\n4. Teste de agregação total...")
    start_time = time.time()
    try:
        response = requests.get(f"{SALES_API_URL}/sales/aggregate", params={"group_by": "total", "period": "daily"})
        end_time = time.time()
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else 0
            tempo = end_time - start_time
            print(f"   ✓ Agregação total: {count} dias")
            print(".2f")
        else:
            print(f"   ✗ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Erro de conexão: {e}")

    print("\n=== TESTE CONCLUÍDO ===")
    print("Para executar este teste manualmente:")
    print("1. Certifique-se que a API está rodando (python -m uvicorn api.sales_api:app --reload --host 0.0.0.0 --port 8000)")
    print("2. Execute: python teste_manual.py")

if __name__ == "__main__":
    teste_manual()
