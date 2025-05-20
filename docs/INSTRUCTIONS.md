# FastAPI Auth System - Instruções de Setup

Este documento fornece as instruções para configurar e executar o projeto FastAPI Auth System localmente usando Docker e Docker Compose.


## Pré-requisitos

- Docker: [Instruções de instalação](https://docs.docker.com/get-docker/)
- Docker Compose: [Instruções de instalação](https://docs.docker.com/compose/install/)

## Configuração Inicial

1.  **Clone o Repositório (se aplicável)**
    Se este projeto estiver em um repositório Git, clone-o para sua máquina local.
    ```bash
    git clone <url_do_repositorio>
    cd nome_do_diretorio_do_projeto
    ```
    Caso contrário, certifique-se de que todos os arquivos gerados estejam na mesma estrutura de diretórios fornecida.

2.  **Crie o Arquivo de Ambiente (`.env`)**
    Copie o arquivo de exemplo `.env.example` para um novo arquivo chamado `.env` na raiz do projeto.
    ```bash
    cp .env.example .env
    ```
    Abra o arquivo `.env` e edite as variáveis de ambiente conforme necessário. As mais importantes para começar são:

    -   `DB_USER`: Usuário do PostgreSQL (padrão: `postgres`)
    -   `DB_PASS`: Senha do PostgreSQL (ex: `your_postgres_password`)
    -   `DB_NAME`: Nome do banco de dados (padrão: `fastapi_auth_db`)
    -   `SECRET_KEY`: Uma chave secreta forte para JWT. Você pode gerar uma com `openssl rand -hex 32`.
    -   `BACKEND_CORS_ORIGINS`: Lista de origens permitidas para CORS (ex: `"http://localhost:3000,http://localhost:8081"`). Para desenvolvimento, `"*"` pode ser usado, mas não é recomendado para produção.
    -   Configurações de Email (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `EMAIL_FROM`, `EMAILS_ENABLED`): Configure se precisar da funcionalidade de envio de emails (ex: para reset de senha).

3.  **Verifique as Configurações do Docker Compose**
    O arquivo `docker-compose.yml` está configurado para usar as variáveis do arquivo `.env`.
    -   O serviço `db` usará `DB_USER`, `DB_PASS`, `DB_NAME` do `.env` ou os padrões definidos no `docker-compose.yml`.
    -   O serviço `app` montará o diretório atual em `/app` no contêiner e usará o `Dockerfile` para construir a imagem. O `DB_HOST` para a aplicação dentro do Docker será `db` (o nome do serviço do banco de dados).

## Executando a Aplicação com Docker Compose

1.  **Construir e Iniciar os Contêineres**
    No terminal, na raiz do projeto (onde o `docker-compose.yml` está localizado), execute:
    ```bash
    docker-compose up -d
    ```
    -   O `-d` executa os contêineres em modo detached (background).
    -   Isso construirá a imagem Docker para o serviço `app` (se ainda não existir ou se o `Dockerfile` ou contexto mudou) e iniciará os serviços `db` e `app`.
    -   O serviço `app` depende da saúde do serviço `db` antes de iniciar.

2.  **Aplicar Migrações do Banco de Dados (Alembic)**
    Após os contêineres estarem em execução, você precisa aplicar as migrações do banco de dados para criar as tabelas.
    Execute o seguinte comando no terminal:
    ```bash
    docker-compose exec app alembic upgrade head
    ```
    -   `docker-compose exec app` executa um comando dentro do contêiner `app`.
    -   `alembic upgrade head` aplica todas as migrações pendentes.
    -   Você precisará rodar este comando na primeira vez e sempre que adicionar novas migrações ao projeto.

3.  **(Opcional) Inicializar Dados no Banco (Ex: Superusuário)**
    Se você configurou `FIRST_SUPERUSER` e `FIRST_SUPERUSER_PASSWORD` no seu arquivo `.env` e deseja criar este usuário inicial (a lógica para isso precisaria ser implementada em `app/core/init_db.py` e chamada, por exemplo, por um script ou comando CLI), você pode executar um script de inicialização. O `app/core/init_db.py` fornecido tem placeholders para essa lógica.
    Se `app/core/init_db.py` estiver configurado para ser executável como um módulo e contiver a lógica de criação do superusuário:
    ```bash
    docker-compose exec app python -m app.core.init_db
    ```
    *Nota: A implementação atual do `init_db.py` não cria o superusuário automaticamente; essa lógica precisaria ser adicionada e testada.* 
    Alternativamente, você pode criar um superusuário através da API de signup (`/api/v1/auth/signup`) e depois promover o usuário a superusuário manualmente no banco de dados ou através de um endpoint de admin, se implementado.

4.  **Acessar a Aplicação**
    A aplicação FastAPI estará disponível em `http://localhost:8000`.
    A documentação interativa da API (Swagger UI) estará em `http://localhost:8000/docs`.
    A documentação alternativa (ReDoc) estará em `http://localhost:8000/redoc`.

## Comandos Úteis do Docker Compose

-   **Parar os contêineres:**
    ```bash
    docker-compose down
    ```
-   **Ver logs da aplicação:**
    ```bash
    docker-compose logs -f app
    ```
-   **Ver logs do banco de dados:**
    ```bash
    docker-compose logs -f db
    ```
-   **Reconstruir a imagem da aplicação (se você fez alterações no Dockerfile ou código fonte que não são refletidas por volumes):**
    ```bash
    docker-compose up -d --build app
    ```
-   **Acessar o shell dentro do contêiner da aplicação:**
    ```bash
    docker-compose exec app /bin/sh  # Ou /bin/bash se disponível
    ```

## Estrutura do Projeto e Onde Modificar

-   **Configurações Gerais:** `app/core/config/settings.py` (agrega todas as settings), variáveis de ambiente no `.env`.
-   **Modelos de Banco de Dados:** `app/models/` (ex: `user.py`, `token.py`).
-   **Migrações (Alembic):** `alembic/versions/`. Para criar uma nova migração após alterar modelos:
    ```bash
    docker-compose exec app alembic revision -m "sua_mensagem_de_migracao" --autogenerate
    ```
    Depois edite o script gerado e aplique com `docker-compose exec app alembic upgrade head`.
-   **Schemas Pydantic (Validação de Dados):** `app/schemas/` (ex: `auth.py`, `user.py`).
-   **Lógica de Negócios/Serviços:** `app/services/` (ex: `auth_service.py`).
-   **Endpoints da API:** `app/api/v1/` (ex: `auth.py`, `users.py`).
-   **Dependências da API (Autenticação, etc.):** `app/api/deps.py`.
-   **Arquivo Principal da Aplicação FastAPI:** `main.py`.
-   **Dockerfile:** `Dockerfile` (define como a imagem Docker da aplicação é construída).
-   **Docker Compose:** `docker-compose.yml` (define os serviços, redes e volumes).

## Testes (Se Incluídos)

Se o projeto incluir testes (ex: com Pytest):
-   Adicione as dependências de teste em `requirements.txt` (ou um `requirements-dev.txt`).
-   Execute os testes dentro do contêiner da aplicação:
    ```bash
    docker-compose exec app pytest
    ```

## Considerações de Produção

-   **Remova `--reload` do comando Uvicorn** no `docker-compose.yml` para o serviço `app`.
-   Considere usar **Gunicorn com workers Uvicorn** para um servidor WSGI/ASGI mais robusto. Exemplo de comando no `docker-compose.yml`:
    ```yaml
    command: ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]
    ```
    (Adicione `gunicorn` ao `requirements.txt` se usar).
-   Certifique-se de que `APP_ENV` no `.env` está configurado para `production`.
-   Use HTTPS.
-   Configure `BACKEND_CORS_ORIGINS` de forma restritiva.
-   Monitore logs e performance.

Lembre-se de que este é um sistema de autenticação e deve ser tratado com cuidado em relação à segurança. Revise todas as configurações de segurança, especialmente `SECRET_KEY` e o manuseio de tokens.
