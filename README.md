# Venda Certa

Sistema de previsão de vendas sazonais para apoio à decisão de estoque e planejamento comercial.

## Tecnologias

- FastAPI para APIs backend
- flask para frontend 
- MySQL para banco de dados
- Prophet para modelos de previsão
- Docker para containerização

## Estrutura do Projeto

- /api: Sales API e Predict API
- /database: Modelos e scripts de povoamento
- /frontend: Flask
- /tests: Testes automatizados
- docker-compose.yml para orquestração

## Como Rodar

### Configuração Inicial
1. Configurar ambiente virtual e instalar dependências:
   ```
   python -m venv venv
   venv\Scripts\activate.bat
   pip install -r requirements.txt
   ```

2. Configurar banco MySQL e ajustar variáveis de ambiente (DATABASE_URL no .env).

3. Executar scripts de criação e povoamento do banco:
   ```
   python database/populate.py
   ```

### Executando o Sistema
**IMPORTANTE:** O projeto tem 3 componentes que precisam rodar simultaneamente para funcionar completamente.

1. **Sales API** (porta 8000 - fornece dados históricos):
   ```
   python -m uvicorn api.sales_api:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Predict API** (porta 8001 - gera previsões):
   ```
   python -m uvicorn api.predict_api:app --reload --host 0.0.0.0 --port 8001

   ```

3. **Frontend** (porta 5000 - interface web):
   ```
   cd frontend; python app.py
   ```
   (Use `;` para PowerShell ou `&&` para cmd.exe)

### Acesso
- **Frontend:** http://127.0.0.1:5000
- **Sales API Docs:** http://127.0.0.1:8000/docs
- **Predict API Docs:** http://127.0.0.1:8001/docs

**Nota:** Se rodar apenas o frontend (`python app.py`), o site abre mas as funcionalidades de previsão não funcionam, pois dependem das APIs rodando em background.

## Testes

Executar testes com:
```
pytest
```

## Documentação

Documentação das APIs disponível via Swagger em:
- http://localhost:8000/docs (Sales API)
- http://localhost:8001/docs (Predict API)
