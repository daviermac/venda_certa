FROM python:3.9

WORKDIR /app

COPY ../requirements.txt .

RUN pip install -r requirements.txt

COPY . .

# Default command, overridden in compose
CMD ["uvicorn", "sales_api:app", "--host", "0.0.0.0", "--port", "8000"]
