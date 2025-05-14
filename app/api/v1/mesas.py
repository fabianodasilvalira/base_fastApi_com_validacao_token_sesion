from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.session import get_db_session
from app.services.mesa_service import create_mesa, get_mesa, get_mesas, update_mesa, delete_mesa
from app.schemas.mesa_schemas import MesaCreate, MesaOut, MesaUpdate

router = APIRouter(prefix="/mesas", tags=["Mesas"])

@router.post("/", response_model=MesaOut)
def criar_mesa(mesa: MesaCreate, db: Session = Depends(get_db_session)):
    """
    Cria uma nova mesa.

    - **mesa**: Dados da nova mesa a ser criada.
    - **return**: Objeto da mesa criada.
    """
    return create_mesa(db=db, mesa=mesa)

@router.get("/{mesa_id}", response_model=MesaOut)
def obter_mesa_por_id(mesa_id: int, db: Session = Depends(get_db_session)):
    """
    Retorna os dados de uma mesa pelo ID.

    - **mesa_id**: ID da mesa que se deseja buscar.
    - **return**: Objeto da mesa encontrada.
    """
    db_mesa = get_mesa(db=db, mesa_id=mesa_id)
    if db_mesa is None:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    return db_mesa

@router.get("/", response_model=list[MesaOut])
def listar_mesas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    """
    Lista todas as mesas cadastradas.

    - **skip**: Número de registros a pular (paginação).
    - **limit**: Número máximo de registros a retornar.
    - **return**: Lista de mesas.
    """
    return get_mesas(db=db, skip=skip, limit=limit)

@router.put("/{mesa_id}", response_model=MesaOut)
def atualizar_mesa(mesa_id: int, mesa_update: MesaUpdate, db: Session = Depends(get_db_session)):
    """
    Atualiza os dados de uma mesa existente.

    - **mesa_id**: ID da mesa que será atualizada.
    - **mesa_update**: Dados atualizados da mesa.
    - **return**: Objeto da mesa atualizada.
    """
    db_mesa = update_mesa(db=db, mesa_id=mesa_id, mesa_update=mesa_update)
    if db_mesa is None:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    return db_mesa

@router.delete("/{mesa_id}", response_model=MesaOut)
def deletar_mesa(mesa_id: int, db: Session = Depends(get_db_session)):
    """
    Deleta uma mesa do sistema.

    - **mesa_id**: ID da mesa que será removida.
    - **return**: Objeto da mesa deletada.
    """
    db_mesa = delete_mesa(db=db, mesa_id=mesa_id)
    if db_mesa is None:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    return db_mesa
