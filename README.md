# 🔐 FastAPI Auth System

Este é um sistema de autenticação robusto utilizando **FastAPI**, com suporte a JWT, gerenciamento de usuários, criação de superusuário automático e estrutura modular com separação clara entre `auth` e `users`.

---

## 🚀 Tecnologias Utilizadas

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [Uvicorn](https://www.uvicorn.org/)
- [Loguru](https://github.com/Delgan/loguru)
- [PostgreSQL] (recomendado) ou SQLite

---

## 📁 Estrutura do Projeto


## ⚙️ Instalação

git clone https://github.com/seu-usuario/fastapi-auth-system.git
cd fastapi-auth-system

python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows

pip install -r requirements.txt

PROJECT_NAME="FastAPI Auth System"
API_V1_STR="/api/v1"

DATABASE_URL="sqlite+aiosqlite:///./app.db"  # Ou sua URL PostgreSQL

FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin123

uvicorn main:app --reload

A aplicação estará disponível em: http://127.0.0.1:8000

Documentação automática:

Swagger: /docs
Redoc: /redoc

POST /api/v1/auth/login/ → Login com retorno de token JWT

GET /api/v1/users/me/ → Usuário autenticado

POST /api/v1/users/ → Criar novo usuário

GET /api/v1/healthcheck → Verificar status do servidor

alembic revision --autogenerate -m "mensagem"
alembic upgrade head

🧙‍♂️ Superusuário
Ao iniciar o projeto com variáveis FIRST_SUPERUSER e FIRST_SUPERUSER_PASSWORD, um usuário administrador será criado automaticamente se ainda não existir.


---

Se quiser, posso complementar com um `requirements.txt` de exemplo, instruções para Docker ou CI/CD. Deseja adicionar algo mais?

