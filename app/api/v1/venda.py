from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.session import get_db_session
from app.models import Venda, Produto, User  # Certifique-se de importar seus modelos
from app.schemas.venda_schema import VendaCreate
from sqlalchemy.exc import IntegrityError
from uuid import UUID

router = APIRouter()

@router.post("/vendas/", response_model=VendaCreate)
def criar_venda(venda: VendaCreate, db: Session = Depends(get_db_session())):
    # Verificando se o usuário existe
    usuario = db.query(User).filter(User.id == venda.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Criando a venda
    nova_venda = Venda(
        valor_total=venda.valor_total,
        data_venda=venda.data_venda,
        usuario_id=venda.usuario_id,
    )

    # Adicionando os produtos à venda
    produtos = db.query(Produto).filter(Produto.id.in_(venda.produtos)).all()
    if not produtos:
        raise HTTPException(status_code=404, detail="Produtos não encontrados")

    nova_venda.produtos = produtos

    try:
        db.add(nova_venda)
        db.commit()
        db.refresh(nova_venda)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro ao criar a venda: " + str(e.orig))

    return nova_venda
