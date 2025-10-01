# Venda Certa

Sistema de previsão de vendas sazonais para apoio à decisão de estoque e planejamento comercial.

## Tecnologias

- FastAPI para APIs backend
- Streamlit para frontend interativo
- MySQL para banco de dados
- Prophet para modelos de previsão
- Docker para containerização

## Estrutura do Projeto

- /api: Sales API e Predict API
- /database: Modelos e scripts de povoamento
- /frontend: Aplicação Streamlit
- /tests: Testes automatizados
- docker-compose.yml para orquestração

## Como Rodar

1. Configurar ambiente virtual e instalar dependências:
   ```
   python -m venv venv

   venv\Scripts\activate.bat

   pip install -r requirements.txt

   ```

2. Configurar banco MySQL e ajustar variáveis de ambiente.

3. Executar scripts de criação e povoamento do banco.

4. Rodar APIs:
   ```
   uvicorn api.sales_api:app --reload
   uvicorn api.predict_api:app --reload
   ```

5. Rodar frontend:
   ```
   streamlit run frontend/app.py
   ```

## Testes

Executar testes com:
```
pytest
```

## Documentação

Documentação das APIs disponível via Swagger em:
- http://localhost:8000/docs (Sales API)
- http://localhost:8001/docs (Predict API)
