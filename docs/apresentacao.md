# Apresentação: Sistema Venda Certa

## Estrutura da Apresentação (15-20 minutos)

### 1. Introdução (2 min)
- **Apresentador:** [Nome do integrante]
- **Objetivo:** Sistema de previsão de vendas sazonais para gestores de estoque.
- **Problema:** Gestores precisam de previsões precisas para evitar falta ou excesso de produtos, considerando sazonalidades e feriados.
- **Solução:** Plataforma integrada com APIs, banco de dados e frontend para visualização e recomendações.

### 2. Arquitetura do Sistema (3 min)
- **Apresentador:** [Nome do integrante]
- **Diagrama:** Mostrar fluxo: Frontend (Flask) → APIs (FastAPI) → Banco (MySQL) + Integrações (BrasilAPI, Google Trends).
- **Componentes:**
  - Sales API: Lista produtos, histórico de vendas, agregações.
  - Predict API: Previsões com Prophet, considerando feriados e sazonalidades.
  - Frontend: Dashboard com gráficos interativos (Plotly), autenticação, tendências de mercado.
  - Banco: Dados simulados (2021-2023, ~13k vendas, 6 produtos em 4 categorias).

### 3. Dados e Modelo de ML (4 min)
- **Apresentador:** [Nome do integrante]
- **Dados:** Simulados com sazonalidades (picos em dezembro/novembro), feriados (Natal, Black Friday), fins de semana. Produtos: Eletrônicos, Roupas, Livros, Móveis.
- **Tratamento:** Normalizados, sem outliers significativos (dados simulados limpos).
- **Modelo:** Prophet (Facebook) para séries temporais. Integra feriados via BrasilAPI. Salva previsões no banco para cache.
- **Exemplo:** Previsão de vendas totais para 30 dias – gráfico histórico vs. previsto com intervalos de confiança.

### 4. Demonstração (5 min)
- **Apresentador:** Todos os integrantes (cada um fala uma parte)
- **Passos:**
  - Rodar APIs (Sales em 8000, Predict em 8001).
  - Abrir frontend (http://localhost:5000).
  - Login (usuário: admin, senha: 123).
  - Selecionar escopo (total/categoria/produto), período (30 dias).
  - Gerar previsão: Gráfico interativo, tabela de recomendações de estoque.
  - Mostrar tendências: Google Trends e simulação Amazon.
- **Resultado:** Previsão ajuda a decidir estoque (ex: +20% em dezembro).

### 5. Desafios e Aprendizados (3 min)
- **Apresentador:** [Nome do integrante]
- **Desafios:** Integração de APIs externas, migração futura para MongoDB Atlas, autenticação segura.
- **Aprendizados:** Uso de FastAPI/Flask, ML com Prophet, bancos relacionais/NoSQL, deploy com Docker.

### 6. Conclusão e Perguntas (3 min)
- **Apresentador:** Todos
- **Próximos Passos:** Deploy em produção, mais integrações (ex: vendas reais).
- **Perguntas:** Abrir para dúvidas.

## Materiais para Upload no NAV
- Slides em PDF (Google Slides exportado).
- Código fonte (ZIP do projeto).
- Dataset exemplo (docs/dataset_exemplo.csv).
- README atualizado com instruções.

## Dicas para Apresentação
- Pratique o demo (garanta que APIs estejam rodando).
- Use imagens/gráficos do dashboard.
- Cada integrante fala claramente, sem ler slides.
- Tempo: Controle com cronômetro.

Se precisar de slides prontos ou ajustes, me avise!
