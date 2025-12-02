# Venda Certa

Sistema de previsão de vendas sazonais para apoio à decisão de estoque e planejamento comercial, utilizando machine learning com Prophet para identificar padrões sazonais e tendências.

## Tecnologias

- **FastAPI** para APIs backend (Sales API e Predict API)
- **Flask** para frontend web
- **MongoDB** para banco de dados NoSQL
- **Prophet** para modelos de previsão de séries temporais
- **Docker** para containerização e isolamento de serviços

## Estrutura do Projeto

- `/api`: Contém `sales_api.py` (porta 8000 - fornece dados históricos) e `predict_api.py` (porta 8001 - gera previsões com Prophet)
- `/database`: Modelos MongoDB (`models_mongo.py`)
- `/frontend`: Aplicação Flask (`app.py`) com templates HTML para dashboards e visualizações
- `docker-compose.yml`: Orquestração dos serviços (MongoDB, APIs e frontend)
- `requirements.txt`: Dependências Python

## Como Rodar

### Opção 1: Usando Docker (Recomendado)
1. Certifique-se de ter Docker e Docker Compose instalados.
2. Execute o comando:
   ```
   docker-compose up
   ```
   Isso iniciará todos os serviços: MongoDB, Sales API, Predict API e Frontend.

### Opção 2: Execução Manual
**IMPORTANTE:** O projeto tem 3 componentes que precisam rodar simultaneamente para funcionar completamente.

1. **Configuração Inicial:**
   - Instalar dependências:
     ```
     pip install -r requirements.txt
     ```
   - Certifique-se de que MongoDB esteja rodando localmente (porta padrão 27017).

2. **Executando os Serviços:**
   - **Sales API** (porta 8000 - fornece dados históricos):
     ```
     python -m uvicorn api.sales_api:app --reload --host 0.0.0.0 --port 8000
     ```
   - **Predict API** (porta 8001 - gera previsões):
     ```
     python -m uvicorn api.predict_api:app --reload --host 0.0.0.0 --port 8001
     ```
   - **Frontend** (porta 5000 - interface web):
     ```
     cd frontend && python app.py
     ```

### Acesso
- **Frontend:** http://127.0.0.1:5000 (Dashboard com dados históricos e previsões)
- **Sales API Docs:** http://127.0.0.1:8000/docs (Swagger para testes de dados históricos)
- **Predict API Docs:** http://127.0.0.1:8001/docs (Swagger para testes de previsões)

**Nota:** Se rodar apenas o frontend, o site abre mas as funcionalidades de previsão não funcionam, pois dependem das APIs rodando em background.

## Funcionalidades

- **Previsão de Vendas:** Geração de previsões diárias para períodos personalizados (ex: 30 ou 180 dias) usando Prophet.
- **Cálculo de Estoque Recomendado:** Média das previsões diárias multiplicada por margem de segurança (20%).
- **Dashboard Interativo:** Visualização de dados históricos, gráficos de previsões e decomposição Prophet (tendência, sazonalidade, feriados).
- **APIs REST:** Endpoints para consulta de dados e geração de previsões com documentação Swagger.

## Testes

Executar testes automatizados com:
```
pytest
```

## Segurança

- Sistema de autenticação de usuários para acesso controlado ao frontend.
- Dados armazenados localmente com isolamento via Docker.
- Validação de entradas nas APIs para prevenir vulnerabilidades.
- Uso de HTTPS recomendado em produção para criptografia de dados.

## Documentação

Documentação completa das APIs disponível via Swagger:
- http://localhost:8000/docs (Sales API)
- http://localhost:8001/docs (Predict API)
