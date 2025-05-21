#!/bin/sh

echo "Aguardando o banco de dados ficar pronto..."
sleep 5

echo "Gerando migrations (caso necessário)..."
alembic revision --autogenerate -m "Criação das tabelas iniciais" || echo "Migration já existe"

echo "Aplicando migrations..."
alembic upgrade head

echo "Iniciando servidor FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
