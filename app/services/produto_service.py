from sqlalchemy.orm import Session
from app.models.produto import Produto
from app.schemas.produto_schemas import ProdutoCreate, ProdutoUpdate
from fastapi import HTTPException


def criar_produto(db: Session, produto: ProdutoCreate):
    try:
        db_produto = Produto(**produto.dict())
        db.add(db_produto)
        db.commit()
        db.refresh(db_produto)
        return db_produto
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar produto: {str(e)}")


def listar_produtos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Produto).offset(skip).limit(limit).all()


def obter_produto(db: Session, produto_id: int):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        return None
    return produto


def atualizar_produto(db: Session, produto_id: int, produto: ProdutoUpdate):
    db_produto = obter_produto(db, produto_id)
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    try:
        update_data = produto.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_produto, key, value)
        db.commit()
        db.refresh(db_produto)
        return db_produto
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar produto: {str(e)}")


def deletar_produto(db: Session, produto_id: int):
    db_produto = obter_produto(db, produto_id)
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    try:
        db.delete(db_produto)
        db.commit()
        return db_produto
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao deletar produto: {str(e)}")


def listar_produtos_por_categoria(db: Session, categoria_id: int, skip: int = 0, limit: int = 100):
    return db.query(Produto).filter(Produto.categoria_id == categoria_id).offset(skip).limit(limit).all()
