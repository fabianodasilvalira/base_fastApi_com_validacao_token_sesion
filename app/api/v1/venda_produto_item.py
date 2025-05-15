from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.session import get_db_session
from app.schemas.venda_produto_item import VendaProdutoItemCreate, VendaProdutoItemUpdate, VendaProdutoItemOut
from app.services import venda_produto_item_service

router = APIRouter(prefix="/venda-itens", tags=["Itens de Venda"])


@router.post("/", response_model=VendaProdutoItemOut)
def adicionar_item(item: VendaProdutoItemCreate, db: Session = Depends(get_db_session)):
    return venda_produto_item_service.create_item(db, item)


@router.get("/{venda_id}", response_model=list[VendaProdutoItemOut])
def listar_itens(venda_id: int, db: Session = Depends(get_db_session())):
    return venda_produto_item_service.get_itens_by_venda(db, venda_id)


@router.put("/{venda_id}/{produto_id}", response_model=VendaProdutoItemOut)
def atualizar_item(venda_id: int, produto_id: int, item: VendaProdutoItemUpdate, db: Session = Depends(get_db_session)):
    return venda_produto_item_service.update_item(db, venda_id, produto_id, item)


@router.delete("/{venda_id}/{produto_id}")
def remover_item(venda_id: int, produto_id: int, db: Session = Depends(get_db_session)):
    return venda_produto_item_service.delete_item(db, venda_id, produto_id)
