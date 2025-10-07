import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import hashlib
import json
import os
import random
from pytrends.request import TrendReq
import boto3

# ======== CONFIGURAÇÃO DAS APIS ========
PREDICT_API_URL = "http://localhost:8001"
SALES_API_URL = "http://localhost:8000"

# ======== CONFIGURAÇÃO AMAZON E GOOGLE ========
AWS_REGION = "us-east-1"
pytrends = TrendReq(hl='pt-BR', tz=180)

# Inicializar cliente da AWS (simulando integração com Amazon Product Advertising API)
try:
    s3 = boto3.client('s3', region_name=AWS_REGION)
except Exception as e:
    s3 = None
    st.warning("AWS não configurada completamente: recursos de sugestão limitados.")

# ======== AUTENTICAÇÃO LOCAL SIMPLES ========
USER_FILE = "users.json"

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ======== FUNÇÕES DE MERCADO ========
def get_google_trends():
    try:
        pytrends.build_payload(kw_list=["compras online", "promoções", "ofertas", "produtos em alta"], cat=0, timeframe='today 1-m', geo='BR', gprop='')
        data = pytrends.interest_over_time()
        if not data.empty:
            data = data.reset_index()
            data = data.rename(columns={"date": "Data"})
            return data
    except Exception as e:
        st.warning(f"Erro ao consultar Google Trends: {e}")
    return pd.DataFrame()

def get_amazon_trends():
    # Simulação de API de tendências da Amazon
    trends = [
        {"produto": "Smartwatch", "categoria": "Tecnologia", "crescimento": "+45%"},
        {"produto": "Fones Bluetooth", "categoria": "Eletrônicos", "crescimento": "+37%"},
        {"produto": "Tênis esportivo", "categoria": "Moda", "crescimento": "+28%"},
        {"produto": "Air Fryer", "categoria": "Casa", "crescimento": "+32%"},
        {"produto": "Notebook Gamer", "categoria": "Informática", "crescimento": "+25%"}
    ]
    random.shuffle(trends)
    return trends[:3]

# ======== INTERFACE LOGIN ========
def login_screen():
    st.title("Venda Certa - Acesso ao Sistema")
    menu = st.sidebar.selectbox("Menu", ["Login", "Cadastro"])
    users = load_users()

    if menu == "Cadastro":
        st.subheader("Criar nova conta")
        new_user = st.text_input("Usuário")
        new_pass = st.text_input("Senha", type="password")

        if st.button("Cadastrar"):
            if new_user in users:
                st.error("Usuário já existe.")
            elif not new_user or not new_pass:
                st.warning("Preencha todos os campos.")
            else:
                users[new_user] = hash_password(new_pass)
                save_users(users)
                st.success("Cadastro realizado com sucesso! Vá até a aba Login.")

    elif menu == "Login":
        st.subheader("Entrar na conta")
        user = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            if user in users and users[user] == hash_password(password):
                st.success(f"Bem-vindo, {user}!")
                st.session_state["user"] = user
            else:
                st.error("Usuário ou senha incorretos.")

# ======== DASHBOARD DE VENDAS E TENDÊNCIAS ========
def prediction_dashboard():
    st.title("Venda Certa - Previsões e Tendências")

    if st.button("Sair"):
        st.session_state.pop("user")
        st.experimental_rerun()

    col1, col2 = st.columns([2, 1])

    with col1:
        scope = st.selectbox("Escopo da Previsão", ["total", "category", "product"])
        scope_id = None

        if scope == "category":
            try:
                response = requests.get(f"{SALES_API_URL}/products")
                if response.status_code == 200:
                    products = response.json()
                    categories = list(set(p['category'] for p in products))
                    scope_id = st.selectbox("Categoria", categories)
            except:
                st.error("Erro ao carregar categorias")

        elif scope == "product":
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
                    hist_params = {}
                    if scope == "category":
                        hist_params["category"] = scope_id
                    elif scope == "product":
                        hist_params["product_id"] = scope_id

                    hist_response = requests.get(f"{SALES_API_URL}/sales/aggregate", params={**hist_params, "group_by": scope if scope != "total" else "total", "period": "daily"})
                    hist_data = []
                    if hist_response.status_code == 200:
                        hist_data = hist_response.json()

                    hist_df = pd.DataFrame(hist_data)
                    if not hist_df.empty:
                        hist_df['date'] = pd.to_datetime(hist_df['date'] if 'date' in hist_df else hist_df['month'])
                        hist_df = hist_df.rename(columns={'total_quantity': 'quantity'})

                    pred_df = pd.DataFrame(data['predictions'])
                    pred_df['date'] = pd.to_datetime(pred_df['date'])

                    fig = go.Figure()
                    if not hist_df.empty:
                        fig.add_trace(go.Scatter(x=hist_df['date'], y=hist_df['quantity'], mode='lines', name='Histórico'))
                    fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['predicted_value'], mode='lines', name='Previsão'))
                    fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['lower_bound'], fill=None, mode='lines', line_color='lightblue', name='Limite Inferior'))
                    fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['upper_bound'], fill='tonexty', mode='lines', line_color='lightblue', name='Limite Superior'))

                    st.plotly_chart(fig)
                    st.subheader("Previsões Detalhadas")
                    st.dataframe(pred_df[['date', 'predicted_value', 'lower_bound', 'upper_bound']])

                    csv = pred_df.to_csv(index=False)
                    st.download_button("Baixar Previsões em CSV", csv, "previsoes.csv", "text/csv")

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

    with col2:
        st.subheader("🔥 Tendências do Mercado")

        google_data = get_google_trends()
        if not google_data.empty:
            st.line_chart(google_data.set_index("Data"))

        amazon_trends = get_amazon_trends()
        st.write("### Produtos em Alta na Amazon:")
        for trend in amazon_trends:
            st.markdown(f"- *{trend['produto']}* ({trend['categoria']}) – {trend['crescimento']}")

# ======== CONTROLE DE ACESSO ========
if "user" not in st.session_state:
    login_screen()
else:
    prediction_dashboard()
