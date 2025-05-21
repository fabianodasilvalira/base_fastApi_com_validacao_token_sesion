# Dockerfile otimizado para produção

# --- Estágio de Build ---
FROM python:3.10-slim-buster AS builder

WORKDIR /app

# Variáveis de ambiente para evitar prompts interativos durante o build
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalar dependências do sistema operacional necessárias para compilar algumas libs Python
# e para o cliente PostgreSQL (psycopg2-binary)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/* \
    chmod +x /app/entrypoint.sh

# Copiar o arquivo de requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Criar um ambiente virtual e instalar dependências
# Usar um ambiente virtual dentro do contêiner é uma boa prática para isolamento
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependências no ambiente virtual
# --no-cache-dir para reduzir o tamanho da imagem
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante da aplicação
COPY . .

# --- Estágio de Produção ---
FROM python:3.10-slim-buster AS production

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalar apenas as dependências de runtime do PostgreSQL
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copiar o ambiente virtual do estágio de build
COPY --from=builder /opt/venv /opt/venv

# Copiar a aplicação do estágio de build
# Isso garante que apenas o código necessário e as dependências instaladas sejam incluídos
COPY --from=builder /app /app

# Definir o caminho para o ambiente virtual
ENV PATH="/opt/venv/bin:$PATH"

# Expor a porta que a aplicação FastAPI usará (padrão Uvicorn é 8000)
EXPOSE 8000

# Comando para rodar a aplicação com Uvicorn
# O host 0.0.0.0 torna a aplicação acessível de fora do contêiner
# --reload não é recomendado para produção; remova-o ou use apenas para desenvolvimento
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# Para produção, considere mais workers, dependendo dos recursos da sua máquina:
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Onde modificar configurações:
# - Variáveis de ambiente: Podem ser passadas para o contêiner no runtime (e.g., via docker-compose.yml ou `docker run -e VAR=value`).
#   O arquivo .env é lido pela aplicação FastAPI (via pydantic-settings), não diretamente pelo Dockerfile em produção.
# - `main.py`: Contém a inicialização da aplicação FastAPI.
# - `app/core/config/settings.py`: Gerencia as configurações da aplicação.

# Instruções de Build e Run (exemplo):
# 1. Construir a imagem Docker:
#    `docker build -t fastapi-auth-app .`
# 2. Rodar o contêiner (exemplo básico):
#    `docker run -d -p 8000:8000 --name my-fastapi-app -e APP_ENV="production" -e SECRET_KEY="your_secret_key_here" ... fastapi-auth-app`
#    (É melhor gerenciar variáveis de ambiente com docker-compose ou arquivos .env específicos para o contêiner)
# 3. Para usar com docker-compose.yml (recomendado):
#    Defina os serviços e variáveis de ambiente no `docker-compose.yml` e use `docker-compose up -d`.

# Comando padrão para iniciar a aplicação (pode ser sobrescrito no docker-compose.yml)
# Usando gunicorn como um servidor WSGI mais robusto para produção
# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "./gunicorn_conf.py", "main:app"]
# Se for usar gunicorn, adicione gunicorn ao requirements.txt e crie um gunicorn_conf.py
# Por simplicidade, vamos manter uvicorn diretamente por enquanto, mas gunicorn é uma boa prática para produção.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

