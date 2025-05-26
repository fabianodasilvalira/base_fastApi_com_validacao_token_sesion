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

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

