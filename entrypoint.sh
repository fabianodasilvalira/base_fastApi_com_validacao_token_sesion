#!/bin/sh

set -e

echo "Aplicando migrations com Alembic..."

#alembic revision --autogenerate -m "Create initial tables"
#
#alembic upgrade head

echo "Iniciando servidor FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}


