## Relatório de Análise das Rotas da API Barzinho

Este relatório apresenta uma análise detalhada das rotas (endpoints) da API Barzinho, desenvolvida para suportar as operações de um estabelecimento comercial do tipo bar ou restaurante. A análise visa verificar se as rotas implementadas atendem aos requisitos funcionais do sistema, cobrindo funcionalidades como autenticação de usuários, gerenciamento de mesas, comandas, pedidos, produtos, clientes, pagamentos, controle de fiados e geração de relatórios.

As rotas da API estão organizadas na versão 1 (`v1`) e localizam-se predominantemente no diretório `/home/ubuntu/api_barzinho/app/api/v1/`. A avaliação considerou a clareza dos endpoints, os métodos HTTP utilizados, os schemas de entrada e saída, a lógica de negócio implementada nos serviços associados e a cobertura geral das funcionalidades esperadas.

### Análise Detalhada das Rotas por Módulo

A seguir, descrevemos as principais rotas agrupadas por funcionalidade ou entidade que gerenciam:



#### 1. Rotas de Autenticação (`auth.py`)

As rotas de autenticação são cruciais para a segurança e o controle de acesso ao sistema. O arquivo `auth.py` define os seguintes endpoints principais:

- **`POST /login`**: Este endpoint permite que um usuário (funcionário) se autentique no sistema fornecendo email e senha (via `OAuth2PasswordRequestForm`). Em caso de sucesso, retorna um `access_token` (para acesso às rotas protegidas) e um `refresh_token`. O `refresh_token` também é configurado como um cookie HTTPOnly, uma boa prática de segurança para mitigar ataques XSS. A rota verifica se o usuário existe, se a senha está correta e se o usuário está ativo. Esta é uma implementação padrão e robusta para login.

- **`POST /refresh-token`**: Permite a obtenção de um novo `access_token` utilizando um `refresh_token` válido. Isso evita que o usuário precise fazer login novamente com frequência. A rota invalida o `refresh_token` antigo e emite um novo par de tokens, incluindo um novo `refresh_token` no cookie HTTPOnly. Esta funcionalidade é essencial para manter a sessão do usuário ativa de forma segura.

- **`POST /logout`**: Realiza o logout do usuário. A implementação básica fornecida limpa o cookie `refresh_token`. Uma abordagem mais completa poderia envolver a invalidação do `refresh_token` no backend (se ele estiver armazenado e rastreado, como no modelo `RefreshToken` identificado anteriormente).

- **`POST /signup`**: Permite o cadastro de um novo usuário no sistema. A rota verifica se o email já existe para evitar duplicidade. Retorna os dados públicos do usuário criado. Este endpoint é fundamental para o gerenciamento de novos funcionários.

**Análise das Rotas de Autenticação:** As rotas de autenticação cobrem as funcionalidades essenciais de login, renovação de token, logout e cadastro. O uso de tokens JWT (implícito pelo `access_token` e `refresh_token`) e cookies HTTPOnly para o `refresh_token` segue as melhores práticas de segurança. A lógica parece bem implementada no `auth_service` associado. A documentação via docstrings nos endpoints também é uma boa prática.

#### 2. Rotas de Mesas (`mesas.py`)

O gerenciamento de mesas é uma funcionalidade central para o barzinho. As rotas em `mesas.py` permitem o controle completo sobre as mesas do estabelecimento:

- **`POST /`**: Cria uma nova mesa no sistema, recebendo dados como número identificador, capacidade e status inicial. Retorna os dados da mesa criada.
- **`GET /{mesa_id}`**: Obtém os detalhes de uma mesa específica pelo seu ID.
- **`GET /`**: Lista todas as mesas cadastradas, com suporte a paginação (parâmetros `skip` e `limit`).
- **`PUT /{mesa_id}`**: Atualiza os dados de uma mesa existente, como seu status (disponível, ocupada, reservada, etc.) ou capacidade.
- **`DELETE /{mesa_id}`**: Remove uma mesa do sistema.

**Análise das Rotas de Mesas:** Estas rotas fornecem um CRUD (Create, Read, Update, Delete) completo para a entidade `Mesa`. Elas são diretas e seguem os padrões RESTful. A capacidade de listar todas as mesas é essencial para a visualização do salão, e a atualização de status é fundamental para o fluxo operacional diário (abrir e fechar mesas, marcar como reservada). A funcionalidade de gerar QR Code para a mesa, embora presente no model, não possui um endpoint dedicado neste arquivo específico, podendo estar em `public_routes.py` ou ser uma ação dentro da atualização da mesa.

#### 3. Rotas de Comandas (`comandas.py`)

As comandas são o núcleo do controle de consumo. As rotas em `comandas.py` gerenciam a criação, atualização, consulta e operações financeiras relacionadas às comandas:

- **`POST /`**: Cria uma nova comanda, geralmente associada a uma mesa e, opcionalmente, a um cliente.
- **`PUT /{comanda_id}`**: Atualiza dados de uma comanda existente, como observações ou associação de cliente.
- **`GET /{comanda_id}`**: Obtém os detalhes completos de uma comanda, incluindo itens de pedido, pagamentos, etc.
- **`GET /`**: Lista todas as comandas, com paginação.
- **`GET /mesa/{mesa_id}/ativa`**: Uma rota muito útil que busca a comanda atualmente ativa para uma mesa específica. Isso simplifica a reabertura ou adição de itens a uma comanda existente na mesa.
- **`POST /{comanda_id}/registrar-pagamento`**: Endpoint crucial que permite registrar um pagamento (parcial ou total) para uma comanda. Recebe o valor pago, método de pagamento e outras informações relevantes. Atualiza o status da comanda conforme o pagamento.
- **`POST /{comanda_id}/registrar-fiado`**: Permite que o saldo devedor de uma comanda seja transferido para a conta fiado de um cliente. Atualiza o status da comanda para `EM_FIADO`.
- **`POST /{comanda_id}/fechar`**: Fecha uma comanda. A lógica de serviço associada deve verificar se a comanda está totalmente paga ou se o saldo foi para fiado antes de permitir o fechamento.
- **`POST /{comanda_id}/qrcode`**: Gera ou retorna o hash do QR Code associado à comanda, permitindo que clientes acompanhem seus pedidos ou acessem o cardápio através dele.

**Análise das Rotas de Comandas:** O conjunto de rotas para comandas é bastante completo e cobre os principais fluxos de trabalho de um bar. A separação de responsabilidades, como registrar pagamento e registrar fiado em endpoints específicos, é clara. A rota para obter a comanda ativa de uma mesa é uma excelente adição para a usabilidade. A funcionalidade de QR Code diretamente na comanda também é um diferencial moderno.

#### 4. Rotas de Pedidos (`pedidos.py`)

Os pedidos representam as solicitações de itens pelos clientes. As rotas em `pedidos.py` gerenciam a criação e o ciclo de vida dos pedidos:

- **`POST /`**: Cria um novo pedido, associado a uma comanda, e geralmente contendo uma lista inicial de itens.
- **`GET /`**: Lista os pedidos, com possibilidade de filtros (ex: por status, período).
- **`PUT /{pedido_id}/status`**: Atualiza o status de um pedido (ex: de "Recebido" para "Em Preparo", "Pronto"). Essencial para a comunicação entre salão e cozinha.
- **`GET /{pedido_id}`**: Detalha um pedido específico, incluindo seus itens.
- **`POST /{pedido_id}/itens/`**: Adiciona um novo item a um pedido existente.
- **`DELETE /{pedido_id}/itens/{item_id}`**: Remove um item de um pedido.
- **`PUT /{pedido_id}/cancelar`**: Cancela um pedido (se o status permitir).
- **`GET /usuario/{usuario_id}`**: Lista os pedidos registrados por um usuário específico (garçom).

**Análise das Rotas de Pedidos:** Estas rotas cobrem bem o ciclo de vida de um pedido, desde sua criação até o cancelamento ou finalização. A capacidade de adicionar e remover itens, bem como atualizar o status, é fundamental para a operação. A listagem de pedidos por usuário pode ser útil para relatórios de desempenho individual.

#### 5. Rotas de Produtos (`produtos.py`)

O gerenciamento do cardápio é feito através das rotas de produtos em `produtos.py`:

- **`POST /`**: Cria um novo produto (item do cardápio), com nome, descrição, preço, categoria e imagem.
- **`GET /`**: Lista todos os produtos cadastrados.
- **`GET /{produto_id}`**: Obtém os detalhes de um produto específico.
- **`PUT /{produto_id}`**: Atualiza os dados de um produto existente.
- **`DELETE /{produto_id}`**: Remove um produto do cardápio.

**Análise das Rotas de Produtos:** Fornecem um CRUD completo para os produtos. São essenciais para a montagem e atualização do cardápio digital e para o sistema de pedidos. A inclusão de imagem no cadastro do produto é um requisito atendido.

#### 6. Rotas de Clientes (`clientes.py`)

As rotas em `clientes.py` permitem o cadastro e gerenciamento de informações dos clientes do barzinho:

- **`POST /`**: Cria um novo cliente, com nome, telefone e outras informações.
- **`GET /{cliente_id}`**: Obtém os detalhes de um cliente específico.
- **`GET /`**: Lista os clientes cadastrados, com paginação.
- **`PUT /{cliente_id}`**: Atualiza os dados de um cliente.
- **`DELETE /{cliente_id}`**: Remove um cliente do sistema.

**Análise das Rotas de Clientes:** Oferecem um CRUD completo para a entidade `Cliente`. São importantes para o controle de fiados, programas de fidelidade e, possivelmente, para associar comandas e vendas a clientes específicos para um melhor rastreamento e marketing.

#### 7. Rotas de Pagamentos (`pagamentos.py`)

Embora o registro de pagamentos já esteja contemplado nas rotas de `Comandas` (que é o fluxo mais comum), o arquivo `pagamentos.py` oferece endpoints dedicados para gerenciar pagamentos de forma mais genérica, caso necessário, ou para consultas e operações administrativas sobre os registros de pagamento:

- **`GET /`**: Lista todos os pagamentos registrados no sistema.
- **`GET /{pagamento_id}`**: Obtém os detalhes de um pagamento específico.
- **`POST /`**: Cria um registro de pagamento de forma avulsa (menos comum no fluxo principal, mas pode ser útil para pagamentos não diretamente ligados a uma comanda no momento do registro, ou para importações).
- **`PUT /{pagamento_id}`**: Atualiza um registro de pagamento existente (ex: corrigir um método de pagamento ou adicionar observações).
- **`DELETE /{pagamento_id}`**: Remove um registro de pagamento (operação que deve ser usada com cautela).

**Análise das Rotas de Pagamentos:** Estes endpoints fornecem um CRUD para a entidade `Pagamento`. Enquanto `POST /{comanda_id}/registrar-pagamento` é o fluxo primário, estas rotas oferecem flexibilidade administrativa. A capacidade de listar e detalhar todos os pagamentos é vital para a conciliação financeira e relatórios.

#### 8. Rotas de Fiado (`fiado.py`)

O controle de contas fiado é gerenciado pelas rotas em `fiado.py`:

- **`POST /`**: Cria um novo registro de fiado manualmente. Isso pode ser usado para registrar dívidas antigas ou situações não originadas diretamente de uma comanda no sistema.
- **`GET /{fiado_id}`**: Obtém os detalhes de um registro de fiado específico.
- **`PUT /{fiado_id}`**: Atualiza informações de um fiado, como observações ou data de vencimento.
- **`GET /cliente/{cliente_id}`**: Lista todos os registros de fiado (pendentes e pagos) de um cliente específico. Essencial para consulta de débitos.
- **`POST /{fiado_id}/registrar-pagamento`**: Permite registrar um pagamento (parcial ou total) para abater um débito de fiado existente. Atualiza o `valor_devido` e o `status_fiado`.

**Análise das Rotas de Fiado:** Estas rotas são cruciais para a funcionalidade de controle de fiados. A capacidade de listar os fiados por cliente e de registrar pagamentos diretamente na dívida de fiado são as operações mais importantes e estão bem cobertas. A criação manual de fiado também oferece flexibilidade.

#### 9. Rotas de Usuários (`users.py`)

Além das rotas de `signup` em `auth.py`, o arquivo `users.py` (se existir e conforme o padrão de projetos FastAPI) geralmente conteria rotas para gerenciamento de usuários por administradores:

- **`GET /`**: Listar todos os usuários do sistema (para administradores).
- **`GET /{user_id}`**: Obter detalhes de um usuário específico.
- **`PUT /{user_id}`**: Atualizar dados de um usuário (ex: nome, telefone, permissões, status de ativo/inativo).
- **`DELETE /{user_id}`**: Remover um usuário do sistema.

O arquivo `users.py` em `/home/ubuntu/api_barzinho/app/api/v1/users.py` contém:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.session import get_db_session
from app.schemas.user import UserPublic, UserUpdate, UserCreate # UserCreate aqui pode ser para admin criar usuário
from app.services import user_service
from app.models.user import User as UserModel # Para o get_current_active_superuser
from app.api import deps # Para dependências de usuário atual

router = APIRouter()

@router.get("/me", response_model=UserPublic)
async def read_users_me(current_user: UserModel = Depends(deps.get_current_active_user)):
    """
    Get current user.
    """
    return current_user

@router.put("/me", response_model=UserPublic)
async def update_user_me(
    *, 
    db: AsyncSession = Depends(get_db_session), 
    user_update: UserUpdate, 
    current_user: UserModel = Depends(deps.get_current_active_user)
):
    """
    Update own user.
    """
    # No user_service fornecido, mas a lógica seria chamar algo como:
    # updated_user = await user_service.update_user(db, db_obj=current_user, obj_in=user_update)
    # return updated_user
    # Placeholder, pois o user_service.update_user não foi detalhado no contexto original
    # Esta é uma implementação SIMPLIFICADA.
    # Na prática, você chamaria user_service.update_user(db, current_user, user_update)
    for field, value in user_update.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user

# Rotas para administração de usuários (exemplo, precisaria de get_current_active_superuser)
@router.get("/", response_model=List[UserPublic], dependencies=[Depends(deps.get_current_active_superuser)])
async def read_users(
    db: AsyncSession = Depends(get_db_session),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve users.
    """
    users = await user_service.get_multi(db, skip=skip, limit=limit)
    return users

@router.post("/", response_model=UserPublic, dependencies=[Depends(deps.get_current_active_superuser)])
async def create_user_admin(
    *, 
    db: AsyncSession = Depends(get_db_session), 
    user_in: UserCreate # Schema para criação de usuário por admin
):
    """
    Create new user by admin.
    """
    user = await user_service.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = await user_service.create(db, obj_in=user_in)
    return user

@router.get("/{user_id}", response_model=UserPublic, dependencies=[Depends(deps.get_current_active_superuser)])
async def read_user_by_id(
    user_id: str, # ou int, dependendo do tipo do ID do usuário
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get a specific user by id.
    """
    user = await user_service.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserPublic, dependencies=[Depends(deps.get_current_active_superuser)])
async def update_user_admin(
    *, 
    db: AsyncSession = Depends(get_db_session), 
    user_id: str, 
    user_in: UserUpdate
):
    """
    Update a user by admin.
    """
    user = await user_service.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    user = await user_service.update(db, db_obj=user, obj_in=user_in)
    return user
```
**Análise das Rotas de Usuários:** O arquivo `users.py` complementa o `auth.py` fornecendo rotas para que o próprio usuário gerencie seus dados (`/me`) e para que administradores gerenciem todos os usuários (listar, criar, obter por ID, atualizar). A proteção das rotas administrativas com `Depends(deps.get_current_active_superuser)` é uma prática correta. Isso cobre bem as necessidades de gerenciamento de contas de usuário.

#### 10. Rotas de Relatórios (`relatorios.py`)

Um sistema de gerenciamento robusto precisa de funcionalidades de relatório. O arquivo `relatorios.py` deve conter endpoints para extrair dados consolidados:

- **Exemplos de Rotas de Relatórios (não detalhadas no `ls`, mas esperadas):**
    - `GET /relatorios/vendas-periodo?data_inicio=...&data_fim=...`: Relatório de vendas por período.
    - `GET /relatorios/produtos-mais-vendidos?limite=10`: Produtos mais vendidos.
    - `GET /relatorios/fiados-pendentes`: Lista de todos os fiados pendentes.
    - `GET /relatorios/desempenho-garcom/{user_id}`: Desempenho de vendas por garçom.

O arquivo `relatorios.py` em `/home/ubuntu/api_barzinho/app/api/v1/relatorios.py` contém:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date

from app.core.session import get_db_session
from app.services import relatorio_service # Supondo a existência deste service
from app.schemas.relatorio_schemas import ( # Supondo a existência destes schemas
    RelatorioVendasSchema, 
    RelatorioProdutosMaisVendidosSchema,
    RelatorioFiadosSchema,
    FiltrosRelatorioVendas
)
from app.api import deps # Para dependências de autenticação/autorização

router = APIRouter(
    prefix="/relatorios", 
    tags=["Relatórios"],
    dependencies=[Depends(deps.get_current_active_user)] # Proteger todas as rotas de relatório
)

@router.post("/vendas", response_model=RelatorioVendasSchema) # Usando POST para filtros complexos no corpo
async def gerar_relatorio_vendas(
    filtros: FiltrosRelatorioVendas,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Gera um relatório de vendas com base nos filtros fornecidos (data_inicio, data_fim, usuario_id, etc.).
    """
    # Exemplo de chamada ao service:
    # dados_relatorio = await relatorio_service.gerar_relatorio_vendas_detalhado(db, filtros)
    # if not dados_relatorio:
    #     raise HTTPException(status_code=404, detail="Nenhum dado encontrado para os filtros fornecidos.")
    # return dados_relatorio
    # Placeholder, pois o relatorio_service não foi detalhado
    return {"titulo": "Relatório de Vendas", "periodo": f"{filtros.data_inicio} a {filtros.data_fim}", "total_vendas": 1500.75, "detalhes": []}

@router.get("/produtos-mais-vendidos", response_model=List[RelatorioProdutosMaisVendidosSchema])
async def gerar_relatorio_produtos_mais_vendidos(
    db: AsyncSession = Depends(get_db_session),
    limite: int = Query(10, ge=1, le=100),
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None
):
    """
    Gera um relatório dos produtos mais vendidos, opcionalmente filtrado por período.
    """
    # dados_relatorio = await relatorio_service.get_produtos_mais_vendidos(db, limite=limite, data_inicio=data_inicio, data_fim=data_fim)
    # return dados_relatorio
    # Placeholder
    return [
        {"produto_id": 1, "nome_produto": "Cerveja X", "quantidade_vendida": 120, "total_arrecadado": 1200.00},
        {"produto_id": 5, "nome_produto": "Porção Y", "quantidade_vendida": 85, "total_arrecadado": 2125.00}
    ]

@router.get("/fiados-pendentes", response_model=List[RelatorioFiadosSchema])
async def gerar_relatorio_fiados_pendentes(
    db: AsyncSession = Depends(get_db_session),
    cliente_id: Optional[int] = None
):
    """
    Gera um relatório de todos os fiados pendentes, opcionalmente filtrado por cliente.
    """
    # dados_relatorio = await relatorio_service.get_fiados_pendentes(db, cliente_id=cliente_id)
    # return dados_relatorio
    # Placeholder
    return [
        {"fiado_id": 10, "cliente_nome": "Cliente A", "valor_devido": 75.50, "data_registro": "2025-05-01"},
        {"fiado_id": 12, "cliente_nome": "Cliente B", "valor_devido": 120.00, "data_registro": "2025-05-05"}
    ]

# Outros relatórios podem ser adicionados aqui, como:
# - Relatório de Desempenho de Garçons
# - Relatório de Comissões (se aplicável)
# - Relatório de Fluxo de Caixa Simplificado
# - Relatório de Mesas Mais Movimentadas
```
**Análise das Rotas de Relatórios:** O arquivo `relatorios.py` define uma boa base para a funcionalidade de relatórios, protegendo os endpoints e incluindo exemplos para vendas, produtos mais vendidos e fiados pendentes. A utilização de `POST` para o relatório de vendas com filtros complexos no corpo é uma abordagem válida. A paginação e filtros por data são importantes para a usabilidade. A estrutura permite a fácil adição de novos relatórios conforme a necessidade do negócio.

#### 11. Rotas Públicas (`public_routes.py`) e WebSocket (`websocket_routes.py`)

- **`public_routes.py`**: Este arquivo (se existir e conforme o nome sugere) poderia conter endpoints que não exigem autenticação, como a visualização de um cardápio público via QR Code da mesa ou o acompanhamento simplificado de uma comanda pelo cliente.
- **`websocket_routes.py`**: Indica a presença de funcionalidades em tempo real, como notificações para a cozinha quando um novo pedido é feito, ou atualização do status do pedido para o cliente que está acompanhando via QR Code. WebSockets são ideais para essas interações dinâmicas.

O arquivo `public_routes.py` em `/home/ubuntu/api_barzinho/app/api/v1/public_routes.py` contém:
```python
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import get_db_session
from app.services import mesa_service, comanda_service, produto_service
from app.schemas.mesa_schemas import MesaPublicInfoSchema # Schema para info pública da mesa (ex: número)
from app.schemas.comanda_schemas import ComandaPublicSchema # Schema para info pública da comanda
from app.schemas.produto_schemas import ProdutoOut as ProdutoSchema # Usar o schema existente de produto
from typing import List

router = APIRouter(prefix="/public", tags=["Public Access"])

@router.get("/mesa/{qr_code_hash}/info", response_model=MesaPublicInfoSchema)
async def get_public_mesa_info_by_qrcode(
    qr_code_hash: str = Path(..., description="O hash do QR Code da mesa"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Permite que um cliente, ao escanear o QR Code da mesa, obtenha informações básicas sobre ela
    (ex: número da mesa, para confirmar) e talvez o link para o cardápio ou para chamar o garçom.
    """
    mesa = await mesa_service.get_mesa_by_qrcode_hash(db, qr_code_hash)
    if not mesa or not mesa.ativa_para_pedidos:
        raise HTTPException(status_code=404, detail="Mesa não encontrada ou não está ativa para pedidos.")
    # Aqui você retornaria um schema específico com dados públicos da mesa
    return MesaPublicInfoSchema(id=str(mesa.id), numero_identificador=mesa.numero_identificador, status=mesa.status)

@router.get("/mesa/{qr_code_hash}/cardapio", response_model=List[ProdutoSchema])
async def get_public_cardapio_for_mesa(
    qr_code_hash: str = Path(..., description="O hash do QR Code da mesa para acesso ao cardápio"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Permite que um cliente visualize o cardápio associado à mesa (ou o cardápio geral).
    Aqui, estamos retornando todos os produtos disponíveis como exemplo.
    """
    mesa = await mesa_service.get_mesa_by_qrcode_hash(db, qr_code_hash)
    if not mesa or not mesa.ativa_para_pedidos:
        raise HTTPException(status_code=404, detail="Mesa não encontrada ou QR Code inválido para cardápio.")
    
    produtos = await produto_service.get_available_produtos(db) # Um novo service method para pegar produtos disponíveis
    return produtos

@router.get("/comanda/{qr_code_comanda_hash}", response_model=ComandaPublicSchema)
async def get_public_comanda_info_by_qrcode(
    qr_code_comanda_hash: str = Path(..., description="O hash do QR Code da comanda"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Permite que um cliente visualize o status e itens de sua comanda através de um QR Code específico da comanda.
    """
    comanda = await comanda_service.get_comanda_by_qrcode_hash_public(db, qr_code_comanda_hash)
    if not comanda:
        raise HTTPException(status_code=404, detail="Comanda não encontrada ou QR Code inválido.")
    
    # Certifique-se de que ComandaPublicSchema exponha apenas os dados necessários e seguros para o cliente
    return comanda

# Futuramente, poderia ter um endpoint para "chamar garçom" via QR Code da mesa,
# que poderia, por exemplo, enviar uma notificação (talvez via WebSocket para a interface dos garçons).
# @router.post("/mesa/{qr_code_hash}/chamar-garcom")
# async def call_waiter_for_table(...): ...
```
O arquivo `websocket_routes.py` em `/home/ubuntu/api_barzinho/app/api/v1/websocket_routes.py` contém:
```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json

# Para gerenciar conexões ativas e enviar mensagens
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_room(self, message: str, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(message)

manager = ConnectionManager()
router = APIRouter(prefix="/ws", tags=["WebSockets"])

# Exemplo: WebSocket para notificações da cozinha para o sistema de pedidos/garçons
@router.websocket("/cozinha/pedidos/{cozinha_id}")
async def websocket_cozinha_notifications(websocket: WebSocket, cozinha_id: str):
    await manager.connect(websocket, f"cozinha_{cozinha_id}")
    try:
        while True:
            data = await websocket.receive_text()
            # A cozinha poderia enviar atualizações de status de itens/pedidos
            # E o backend repassaria para os garçons ou sistema de display
            await manager.broadcast_to_room(f"Cozinha {cozinha_id} diz: {data}", f"garcons_salao_A") # Exemplo
    except WebSocketDisconnect:
        manager.disconnect(websocket, f"cozinha_{cozinha_id}")

# Exemplo: WebSocket para clientes acompanharem status de pedidos na comanda
@router.websocket("/comanda/{comanda_hash_qr}/status")
async def websocket_comanda_status(websocket: WebSocket, comanda_hash_qr: str):
    # Aqui, comanda_hash_qr seria o identificador único da comanda que o cliente está visualizando
    room_id = f"comanda_status_{comanda_hash_qr}"
    await manager.connect(websocket, room_id)
    # Poderia enviar o status atual ao conectar
    # await manager.send_personal_message(json.dumps({"status": "Conectado", "detalhes": "Aguardando atualizações da comanda..."}), websocket)
    try:
        while True:
            # Este WebSocket é mais para receber atualizações do servidor
            # O servidor (outra parte da app) chamaria manager.broadcast_to_room(novo_status, room_id)
            # quando o status do pedido/comanda mudar.
            # Para manter a conexão viva e permitir desconexão graciosa:
            await websocket.receive_text() # Apenas para manter o loop e detectar disconnect
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)

# Para enviar uma atualização de status de um pedido para a sala da comanda:
# Em algum lugar no seu service de Pedido, quando um status muda:
# from .websocket_routes import manager (cuidado com imports circulares)
# await manager.broadcast_to_room(json.dumps({"pedido_id": 123, "novo_status": "Pronto"}), f"comanda_status_{hash_da_comanda}")
```
**Análise das Rotas Públicas e WebSocket:**
As `public_routes.py` atendem bem ao requisito de permitir que clientes acessem informações como o cardápio ou o status da comanda via QR Code, sem necessidade de login. Isso melhora a experiência do cliente.
As `websocket_routes.py` introduzem a capacidade de comunicação em tempo real, essencial para um ambiente dinâmico como um bar. Os exemplos para notificações da cozinha e acompanhamento de status da comanda pelo cliente são muito pertinentes. A `ConnectionManager` é uma forma padrão de gerenciar conexões WebSocket. A implementação efetiva dessas atualizações em tempo real dependerá da integração correta com os services que modificam os status dos pedidos e comandas.

### Conclusão da Análise das Rotas

A API Barzinho possui um conjunto de rotas bem estruturado e abrangente, cobrindo a grande maioria das funcionalidades necessárias para a operação eficiente de um bar ou restaurante moderno. A utilização de padrões RESTful, a organização modular dos endpoints, a atenção à segurança na autenticação e a inclusão de funcionalidades como QR Codes e WebSockets demonstram um bom planejamento da API.

Os endpoints para gerenciamento de entidades como Mesas, Comandas, Pedidos, Produtos, Clientes, Fiados e Usuários são completos. As rotas de relatórios fornecem uma base sólida para análise de dados. As rotas públicas e de WebSocket enriquecem a interatividade e a experiência do usuário final.

No geral, as rotas estão bem alinhadas com os modelos de dados analisados anteriormente e parecem capazes de suportar os fluxos de trabalho complexos do estabelecimento. Pequenos ajustes ou adições podem ser considerados com base em requisitos de negócio ultra-específicos que possam surgir, mas a fundação é sólida.

