import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

PREDICT_API_URL = "http://localhost:8001"  # Assumindo porta 8001 para Predict API
SALES_API_URL = "http://localhost:8000"  # Sales API

st.title("Venda Certa - Previsão de Vendas")

# Seleção de escopo
scope = st.selectbox("Escopo da Previsão", ["total", "category", "product"])

scope_id = None
if scope == "category":
    # Buscar categorias disponíveis
    try:
        response = requests.get(f"{SALES_API_URL}/products")
        if response.status_code == 200:
            products = response.json()
            categories = list(set(p['category'] for p in products))
            scope_id = st.selectbox("Categoria", categories)
    except:
        st.error("Erro ao carregar categorias")
elif scope == "product":
    # Buscar produtos disponíveis
    try:
        response = requests.get(f"{SALES_API_URL}/products")
        if response.status_code == 200:
            products = response.json()
            product_options = {p['name']: p['id'] for p in products}
            selected_name = st.selectbox("Produto", list(product_options.keys()))
            scope_id = product_options[selected_name]
    except:
        st.error("Erro ao carregar produtos")

periods = st.slider("Horizonte de Previsão (dias)", 30, 90, 30)

if st.button("Gerar Previsão"):
    try:
        params = {"scope": scope, "periods": periods}
        if scope_id:
            params["scope_id"] = scope_id

        response = requests.get(f"{PREDICT_API_URL}/predict", params=params)
        if response.status_code == 200:
            data = response.json()

            # Buscar histórico para gráfico
            hist_params = {}
            if scope == "category":
                hist_params["category"] = scope_id
            elif scope == "product":
                hist_params["product_id"] = scope_id

            hist_response = requests.get(f"{SALES_API_URL}/sales/aggregate", params={**hist_params, "group_by": scope if scope != "total" else "total", "period": "daily"})
            hist_data = []
            if hist_response.status_code == 200:
                hist_data = hist_response.json()

            # Preparar dados para gráfico
            hist_df = pd.DataFrame(hist_data)
            if not hist_df.empty:
                hist_df['date'] = pd.to_datetime(hist_df['date'] if 'date' in hist_df else hist_df['month'])
                hist_df = hist_df.rename(columns={'total_quantity': 'quantity'})

            pred_df = pd.DataFrame(data['predictions'])
            pred_df['date'] = pd.to_datetime(pred_df['date'])

            # Gráfico
            fig = go.Figure()
            if not hist_df.empty:
                fig.add_trace(go.Scatter(x=hist_df['date'], y=hist_df['quantity'], mode='lines', name='Histórico'))
            fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['predicted_value'], mode='lines', name='Previsão'))
            fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['lower_bound'], fill=None, mode='lines', line_color='lightblue', name='Limite Inferior'))
            fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['upper_bound'], fill='tonexty', mode='lines', line_color='lightblue', name='Limite Superior'))

            st.plotly_chart(fig)

            # Tabela de previsões
            st.subheader("Previsões")
            st.dataframe(pred_df[['date', 'predicted_value', 'lower_bound', 'upper_bound']])

            # Download CSV
            csv = pred_df.to_csv(index=False)
            st.download_button("Baixar Previsões em CSV", csv, "previsoes.csv", "text/csv")

            # Recomendação de estoque
            rec_response = requests.get(f"{PREDICT_API_URL}/recommendation", params=params)
            if rec_response.status_code == 200:
                rec_data = rec_response.json()
                st.subheader("Recomendação de Estoque")
                st.write(f"Média Prevista: {rec_data['average_predicted']:.2f}")
                st.write(f"Estoque Recomendado: {rec_data['recommended_stock']}")

        else:
            st.error("Erro ao gerar previsão")
    except Exception as e:
        st.error(f"Erro: {str(e)}")
