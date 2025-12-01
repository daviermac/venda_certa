from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import random
from pytrends.request import TrendReq
import os

app = Flask(__name__)
app.secret_key = '1910'

# CONFIGURAÇÃO DAS APIS
PREDICT_API_URL = os.getenv("PREDICT_API_URL", "http://localhost:8001")
SALES_API_URL = os.getenv("SALES_API_URL", "http://localhost:8000")

# FUNÇÕES DE MERCADO
def get_google_trends():
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='pt-BR', tz=180)
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
    try:
        response = requests.get(f"{SALES_API_URL}/trends", params={"source": "amazon"})
        if response.status_code == 200:
            trends = response.json()
            return [
                {
                    "produto": t["product_name"],
                    "categoria": t["category"],
                    "crescimento": t["growth_percentage"]
                }
                for t in trends
            ]
    except Exception as e:
        print(f"Erro ao consultar tendências da Amazon: {e}")
    # Fallback para simulação
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
        try:
            response = requests.post(f"{SALES_API_URL}/users/login", params={"username": user, "password": password})
            data = response.json()
            if response.status_code == 200 and data.get("success"):
                session['user'] = user
                return redirect(url_for('dashboard'))
            else:
                flash(data.get("detail", "Erro ao fazer login."))
        except Exception as e:
            flash(f"Erro de conexão: {e}")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']
        try:
            response = requests.post(f"{SALES_API_URL}/users/register", params={"username": user, "password": password})
            data = response.json()
            if response.status_code == 200 and data.get("success"):
                flash("Cadastro realizado com sucesso!")
                return redirect(url_for('login'))
            else:
                flash(data.get("detail", "Erro ao registrar usuário."))
        except Exception as e:
            flash(f"Erro de conexão: {e}")
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

        # Armazenar parâmetros na sessão para a página de previsões
        session['forecast_params'] = {
            'scope': scope,
            'category': category,
            'product': product,
            'product_id': product_options.get(product) if scope == 'product' and product else None,
            'periods': periods
        }

        # Redirecionar para a página de previsões
        return redirect(url_for('predictions'))

    if request.method == 'POST' and 'generate' in request.form:
        params = {"scope": scope, "periods": periods}
        if scope == 'category' and category:
            params["scope_id"] = category
        elif scope == 'product' and product:
            params["scope_id"] = product

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
                    # Formatar dados para o template
                    rec_data = [{
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'predicted_quantity': rec_data.get('average_predicted', 0),
                        'recommended_stock': rec_data.get('recommended_stock', 0),
                        'action': 'comprar' if rec_data.get('recommended_stock', 0) > 0 else 'manter'
                    }]
                else:
                    flash("Erro ao carregar recomendações.")

                # Armazenar dados da geração para reutilização na página de previsões
                session['prediction_data'] = {
                    'predictions': data['predictions'],
                    'historical_data': hist_data,
                    'scope': scope,
                    'scope_id': params.get('scope_id'),
                    'periods': periods,
                    'avg_predicted': rec_data[0]['predicted_quantity'] if rec_data else 0,
                    'recommended_stock': rec_data[0]['recommended_stock'] if rec_data else 0,
                    'scope_title': f"Categoria: {category}" if scope == 'category' and category else f"Produto: {product}" if scope == 'product' and product else "Total de Vendas"
                }

                flash("Previsão gerada com sucesso! Clique em 'Ver Previsões' para visualizar os resultados.")

            else:
                flash("Erro ao gerar previsão.")
        except Exception as e:
            flash(f"Erro de conexão: {e}")

    return render_template('dashboard.html', user=session['user'], graph_html=graph_html, pred_df=pred_df.to_dict(orient='records'), rec_data=rec_data, categories=categories, product_options=product_options, scope=scope, periods=periods)

@app.route('/predictions', methods=['GET', 'POST'])
def predictions():
    if 'user' not in session:
        return redirect(url_for('login'))

    print(f"DEBUG: Rota predictions chamada com method={request.method}")

    # Verificar se há dados de previsão armazenados na sessão (de uma geração anterior no dashboard)
    if 'prediction_data' in session and request.method == 'GET':
        prediction_data = session['prediction_data']
        predictions = prediction_data['predictions']
        hist_data = prediction_data['historical_data']
        scope = prediction_data['scope']
        scope_id = prediction_data['scope_id']
        periods = prediction_data['periods']
        avg_predicted = prediction_data['avg_predicted']
        recommended_stock = prediction_data['recommended_stock']
        scope_title = prediction_data['scope_title']

        print(f"DEBUG: Usando dados armazenados da sessão: scope={scope}, scope_id={scope_id}, periods={periods}")

        # Limpar sessão após usar
        session.pop('prediction_data', None)

        # Processar dados históricos
        hist_df = pd.DataFrame(hist_data)
        if not hist_df.empty:
            hist_df['date'] = pd.to_datetime(hist_df['date'] if 'date' in hist_df else hist_df['month'])
            hist_df = hist_df.rename(columns={'total_quantity': 'quantity'})

        # Processar previsões
        pred_df = pd.DataFrame(predictions)
        if 'date' in pred_df.columns:
            # Datas já vêm formatadas como string da API, converter para datetime para gráficos
            pred_df['date'] = pd.to_datetime(pred_df['date'])
        else:
            pred_df['date'] = pd.to_datetime(pred_df['ds'])
            pred_df = pred_df.drop(columns=['ds'])

        # Adicionar recommended_stock ao pred_df
        pred_df['recommended_stock'] = recommended_stock

        # Criar gráfico histórico
        hist_fig = go.Figure()
        if not hist_df.empty:
            hist_fig.add_trace(go.Scatter(x=hist_df['date'], y=hist_df['quantity'], mode='lines', name='Vendas Históricas', line_color='blue'))
            hist_fig.update_layout(title=f'Histórico de Vendas - {scope_title}', xaxis_title='Data', yaxis_title='Quantidade Vendida')

        historical_graph_html = hist_fig.to_html(full_html=False)

        # Criar gráfico de previsão
        forecast_fig = go.Figure()
        forecast_fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['predicted_value'], mode='lines', name='Previsão', line_color='orange'))
        forecast_fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['recommended_stock'], mode='lines', name='Estoque Recomendado', line_color='green', line_dash='dash'))
        forecast_fig.update_layout(title='Previsão de Vendas com Estoque Recomendado', xaxis_title='Data', yaxis_title='Quantidade')

        forecast_graph_html = forecast_fig.to_html(full_html=False)

        # Converter datas para string para a tabela
        pred_df['date'] = pred_df['date'].dt.strftime('%Y-%m-%d')

        # Atualizar a lista predictions
        predictions = pred_df.to_dict('records')

        # Tendências
        try:
            google_trends = get_google_trends()
        except Exception as e:
            print(f"Erro ao carregar Google Trends: {e}")
            google_trends = pd.DataFrame()

        try:
            amazon_trends = get_amazon_trends()
        except Exception as e:
            print(f"Erro ao carregar Amazon Trends: {e}")
            amazon_trends = []

        return render_template('predictions.html',
                             user=session['user'],
                             scope_title=scope_title,
                             periods=periods,
                             predictions=predictions,
                             historical_graph_html=historical_graph_html,
                             forecast_graph_html=forecast_graph_html,
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
        # Datas já vêm formatadas como string da API, converter para datetime para gráficos
        pred_df['date'] = pd.to_datetime(pred_df['date'])

        # Recomendações
        rec_response = requests.get(f"{PREDICT_API_URL}/recommendation", params=params)
        rec_data = {}
        if rec_response.status_code == 200:
            rec_data = rec_response.json()

        avg_predicted = rec_data.get('average_predicted', 0)
        recommended_stock = rec_data.get('recommended_stock', 0)

        # Adicionar recommended_stock ao pred_df
        pred_df['recommended_stock'] = recommended_stock

        # Criar gráfico histórico
        hist_fig = go.Figure()
        if not hist_df.empty:
            hist_fig.add_trace(go.Scatter(x=hist_df['date'], y=hist_df['quantity'], mode='lines', name='Vendas Históricas', line_color='blue'))
            hist_fig.update_layout(title='Histórico de Vendas', xaxis_title='Data', yaxis_title='Quantidade Vendida')

        historical_graph_html = hist_fig.to_html(full_html=False)

        # Criar gráfico de previsão
        forecast_fig = go.Figure()
        forecast_fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['predicted_value'], mode='lines', name='Previsão', line_color='orange'))
        forecast_fig.add_trace(go.Scatter(x=pred_df['date'], y=pred_df['recommended_stock'], mode='lines', name='Estoque Recomendado', line_color='green', line_dash='dash'))
        forecast_fig.update_layout(title='Previsão de Vendas com Estoque Recomendado', xaxis_title='Data', yaxis_title='Quantidade')

        forecast_graph_html = forecast_fig.to_html(full_html=False)

        # Converter datas para string para a tabela
        pred_df['date'] = pred_df['date'].dt.strftime('%Y-%m-%d')

        # Atualizar a lista predictions
        predictions = pred_df.to_dict('records')

        # Tendências
        try:
            google_trends = get_google_trends()
        except Exception as e:
            print(f"Erro ao carregar Google Trends: {e}")
            google_trends = pd.DataFrame()

        try:
            amazon_trends = get_amazon_trends()
        except Exception as e:
            print(f"Erro ao carregar Amazon Trends: {e}")
            amazon_trends = []

        return render_template('predictions.html',
                             user=session['user'],
                             scope_title=scope_title,
                             periods=periods,
                             predictions=predictions,
                             historical_graph_html=historical_graph_html,
                             forecast_graph_html=forecast_graph_html,
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
