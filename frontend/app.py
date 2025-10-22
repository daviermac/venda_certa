from flask import Flask, render_template, request, redirect, url_for, session, flash
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

app = Flask(__name__)
app.secret_key = '1910'

# CONFIGURAÇÃO DAS APIS
PREDICT_API_URL = "http://localhost:8001"
SALES_API_URL = "http://localhost:8000"

# CONFIGURAÇÃO AMAZON E GOOGLE
AWS_REGION = "us-east-1"
pytrends = TrendReq(hl='pt-BR', tz=180)

# Inicializar cliente da AWS
try:
    s3 = boto3.client('s3', region_name=AWS_REGION)
except Exception as e:
    s3 = None

# AUTENTICAÇÃO LOCAL
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

# FUNÇÕES DE MERCADO
def get_google_trends():
    try:
        pytrends.build_payload(kw_list=["compras online", "promoções", "ofertas", "produtos em alta"], cat=0, timeframe='today 1-m', geo='BR', gprop='')
        data = pytrends.interest_over_time()
        if not data.empty:
            data = data.reset_index()
            data = data.rename(columns={"date": "Data"})
            return data
    except Exception as e:
        print(f"Erro ao consultar Google Trends: {e}")
    return pd.DataFrame()

def get_amazon_trends():
    # Simulação de API
    trends = [
        {"produto": "Smartwatch", "categoria": "Tecnologia", "crescimento": "+45%"},
        {"produto": "Fones Bluetooth", "categoria": "Eletrônicos", "crescimento": "+37%"},
        {"produto": "Tênis esportivo", "categoria": "Moda", "crescimento": "+28%"},
        {"produto": "Air Fryer", "categoria": "Casa", "crescimento": "+32%"},
        {"produto": "Notebook Gamer", "categoria": "Informática", "crescimento": "+25%"}
    ]
    random.shuffle(trends)
    return trends[:3]

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']
        users = load_users()
        if user in users and users[user] == hash_password(password):
            session['user'] = user
            return redirect(url_for('dashboard'))
        else:
            flash("Usuário ou senha incorretos.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']
        users = load_users()
        if user in users:
            flash("Usuário já existe.")
        else:
            users[user] = hash_password(password)
            save_users(users)
            flash("Cadastro realizado com sucesso!")
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    # Carregar categorias e produtos para os selects
    categories = []
    product_options = {}
    try:
        response = requests.get(f"{SALES_API_URL}/products")
        if response.status_code == 200:
            products = response.json()
            categories = list(set(p['category'] for p in products))
            product_options = {p['name']: p['id'] for p in products}
    except Exception as e:
        flash(f"Erro ao carregar dados: {e}")

    scope = request.form.get('scope', 'total')
    periods = int(request.form.get('periods', 30))
    category = request.form.get('category')
    product = request.form.get('product')

    graph_html = None
    rec_data = None
    pred_df = pd.DataFrame()

    if request.method == 'POST' and 'view_predictions' in request.form:
        # Redirecionar para a página de previsões com os parâmetros do formulário
        params = {"scope": scope, "periods": periods}
        if scope == 'category' and category:
            params["scope_id"] = category
        elif scope == 'product' and product:
            params["scope_id"] = product_options.get(product)

        try:
            response = requests.get(f"{PREDICT_API_URL}/predict", params=params)
            if response.status_code == 200:
                data = response.json()

                # Dados históricos
                hist_params = {}
                if scope == "category":
                    hist_params["category"] = category
                elif scope == "product":
                    hist_params["product_id"] = product_options.get(product)

                hist_response = requests.get(f"{SALES_API_URL}/sales/aggregate", params={**hist_params, "group_by": scope if scope != "total" else "total", "period": "daily"})
                hist_data = []
                if hist_response.status_code == 200:
                    hist_data = hist_response.json()

                hist_df = pd.DataFrame(hist_data)
                if not hist_df.empty:
                    hist_df['date'] = pd.to_datetime(hist_df['date'] if 'date' in hist_df else hist_df['month'])
                    hist_df = hist_df.rename(columns={'total_quantity': 'quantity'})

                pred_df = pd.DataFrame(data['predictions'])
                if 'date' in pred_df.columns:
                    pred_df['date'] = pd.to_datetime(pred_df['date'])
                else:
                    pred_df['date'] = pd.to_datetime(pred_df['ds'])

                fig = go.Figure()
                if not hist_df.empty:
                    fig.add_trace(go.Scatter(x=hist_df['date'], y=hist_df['quantity'], mode='lines', name='Histórico'))
                fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['predicted_value'], mode='lines', name='Previsão'))
                fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['lower_bound'], fill=None, mode='lines', line_color='lightblue', name='Limite Inferior'))
                fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['upper_bound'], fill='tonexty', mode='lines', line_color='lightblue', name='Limite Superior'))

                graph_html = fig.to_html(full_html=False)

                # Recomendações
                rec_response = requests.get(f"{PREDICT_API_URL}/recommendation", params=params)
                if rec_response.status_code == 200:
                    rec_data = rec_response.json()
                else:
                    flash("Erro ao carregar recomendações.")

                # Armazenar dados na sessão para redirecionar
                session['forecast_data'] = {
                    'scope': scope,
                    'category': category,
                    'product': product,
                    'periods': periods,
                    'graph_html': graph_html,
                    'rec_data': rec_data,
                    'predictions': data['predictions'],
                    'hist_data': hist_data
                }

                # Redirecionar para a página de previsões
                return redirect(url_for('predictions'))
            else:
                flash("Erro ao gerar previsão.")
        except Exception as e:
            flash(f"Erro de conexão: {e}")

    if request.method == 'POST' and 'generate' in request.form:
        params = {"scope": scope, "periods": periods}
        if scope == 'category' and category:
            params["scope_id"] = category
        elif scope == 'product' and product:
            params["scope_id"] = product_options.get(product)

        try:
            response = requests.get(f"{PREDICT_API_URL}/predict", params=params)
            if response.status_code == 200:
                data = response.json()

                # Dados históricos
                hist_params = {}
                if scope == "category":
                    hist_params["category"] = category
                elif scope == "product":
                    hist_params["product_id"] = product_options.get(product)

                hist_response = requests.get(f"{SALES_API_URL}/sales/aggregate", params={**hist_params, "group_by": scope if scope != "total" else "total", "period": "daily"})
                hist_data = []
                if hist_response.status_code == 200:
                    hist_data = hist_response.json()

                hist_df = pd.DataFrame(hist_data)
                if not hist_df.empty:
                    hist_df['date'] = pd.to_datetime(hist_df['date'] if 'date' in hist_df else hist_df['month'])
                    hist_df = hist_df.rename(columns={'total_quantity': 'quantity'})

                pred_df = pd.DataFrame(data['predictions'])
                if 'date' in pred_df.columns:
                    pred_df['date'] = pd.to_datetime(pred_df['date'])
                else:
                    pred_df['date'] = pd.to_datetime(pred_df['ds'])

                fig = go.Figure()
                if not hist_df.empty:
                    fig.add_trace(go.Scatter(x=hist_df['date'], y=hist_df['quantity'], mode='lines', name='Histórico'))
                fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['predicted_value'], mode='lines', name='Previsão'))
                fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['lower_bound'], fill=None, mode='lines', line_color='lightblue', name='Limite Inferior'))
                fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['upper_bound'], fill='tonexty', mode='lines', line_color='lightblue', name='Limite Superior'))

                graph_html = fig.to_html(full_html=False)

                # Recomendações
                rec_response = requests.get(f"{PREDICT_API_URL}/recommendation", params=params)
                if rec_response.status_code == 200:
                    rec_data = rec_response.json()
                else:
                    flash("Erro ao carregar recomendações.")

            else:
                flash("Erro ao gerar previsão.")
        except Exception as e:
            flash(f"Erro de conexão: {e}")

    return render_template('dashboard.html', user=session['user'], graph_html=graph_html, pred_df=pred_df.to_dict(orient='records'), rec_data=rec_data, categories=categories, product_options=product_options, scope=scope, periods=periods)

@app.route('/predictions', methods=['GET', 'POST'])
def predictions():
    if 'user' not in session:
        return redirect(url_for('login'))

    # Verificar se há dados na sessão (de uma geração anterior)
    if 'forecast_data' in session and request.method == 'GET':
        forecast_data = session['forecast_data']
        scope = forecast_data['scope']
        category = forecast_data['category']
        product = forecast_data['product']
        periods = forecast_data['periods']
        graph_html = forecast_data['graph_html']
        rec_data = forecast_data['rec_data']
        predictions = forecast_data['predictions']
        hist_data = forecast_data['hist_data']

        # Determinar título
        if scope == 'category' and category:
            scope_title = f"Categoria: {category}"
        elif scope == 'product' and product:
            scope_title = f"Produto: {product}"
        else:
            scope_title = "Total de Vendas"

        avg_predicted = rec_data.get('average_predicted', 0) if rec_data else 0
        recommended_stock = rec_data.get('recommended_stock', 0) if rec_data else 0

        # Tendências
        google_trends = get_google_trends()
        amazon_trends = get_amazon_trends()

        return render_template('predictions.html',
                             user=session['user'],
                             scope_title=scope_title,
                             periods=periods,
                             predictions=predictions,
                             graph_html=graph_html,
                             avg_predicted=avg_predicted,
                             recommended_stock=recommended_stock,
                             google_trends=google_trends,
                             amazon_trends=amazon_trends)

    # Se não há dados na sessão ou é POST, processar normalmente
    scope = request.form.get('scope')
    periods = int(request.form.get('periods', 30))
    category = request.form.get('category')
    product = request.form.get('product')

    # Carregar categorias e produtos
    product_options = {}
    try:
        response = requests.get(f"{SALES_API_URL}/products")
        if response.status_code == 200:
            products = response.json()
            product_options = {p['name']: p['id'] for p in products}
    except Exception as e:
        flash(f"Erro ao carregar dados: {e}")
        return redirect(url_for('dashboard'))

    params = {"scope": scope, "periods": periods}
    if scope == 'category' and category:
        params["scope_id"] = category
        scope_title = f"Categoria: {category}"
    elif scope == 'product' and product:
        params["scope_id"] = product_options.get(product)
        scope_title = f"Produto: {product}"
    else:
        scope_title = "Total de Vendas"

    try:
        # Gerar previsão
        response = requests.get(f"{PREDICT_API_URL}/predict", params=params)
        if response.status_code != 200:
            flash("Erro ao gerar previsão.")
            return redirect(url_for('dashboard'))

        data = response.json()
        predictions = data['predictions']

        # Dados históricos para gráfico
        hist_params = {}
        if scope == "category":
            hist_params["category"] = category
        elif scope == "product":
            hist_params["product_id"] = product_options.get(product)

        hist_response = requests.get(f"{SALES_API_URL}/sales/aggregate", params={**hist_params, "group_by": scope if scope != "total" else "total", "period": "daily"})
        hist_data = []
        if hist_response.status_code == 200:
            hist_data = hist_response.json()

        hist_df = pd.DataFrame(hist_data)
        if not hist_df.empty:
            hist_df['date'] = pd.to_datetime(hist_df['date'] if 'date' in hist_df else hist_df['month'])
            hist_df = hist_df.rename(columns={'total_quantity': 'quantity'})

        pred_df = pd.DataFrame(predictions)
        pred_df['date'] = pd.to_datetime(pred_df['date'])

        # Criar gráfico
        fig = go.Figure()
        if not hist_df.empty:
            fig.add_trace(go.Scatter(x=hist_df['date'], y=hist_df['quantity'], mode='lines', name='Histórico'))
        fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['predicted_value'], mode='lines', name='Previsão'))
        fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['lower_bound'], fill=None, mode='lines', line_color='lightblue', name='Limite Inferior'))
        fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['upper_bound'], fill='tonexty', mode='lines', line_color='lightblue', name='Limite Superior'))

        graph_html = fig.to_html(full_html=False)

        # Recomendações
        rec_response = requests.get(f"{PREDICT_API_URL}/recommendation", params=params)
        rec_data = {}
        if rec_response.status_code == 200:
            rec_data = rec_response.json()

        avg_predicted = rec_data.get('average_predicted', 0)
        recommended_stock = rec_data.get('recommended_stock', 0)

        # Tendências
        google_trends = get_google_trends()
        amazon_trends = get_amazon_trends()

        return render_template('predictions.html',
                             user=session['user'],
                             scope_title=scope_title,
                             periods=periods,
                             predictions=predictions,
                             graph_html=graph_html,
                             avg_predicted=avg_predicted,
                             recommended_stock=recommended_stock,
                             google_trends=google_trends,
                             amazon_trends=amazon_trends)

    except Exception as e:
        flash(f"Erro de conexão: {e}")
        return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
