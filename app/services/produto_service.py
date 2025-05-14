from sqlalchemy.orm import Session
from app.models.produto import Produto
from app.schemas.produto_schemas import ProdutoCreate, ProdutoUpdate

def criar_produto(db: Session, produto: ProdutoCreate):
    db_produto = Produto(**produto.dict())
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)
    return db_produto

def listar_produtos(db: Session):
    return db.query(Produto).all()

def obter_produto(db: Session, produto_id: int):
    return db.query(Produto).filter(Produto.id == produto_id).first()

def atualizar_produto(db: Session, produto_id: int, produto: ProdutoUpdate):
    db_produto = obter_produto(db, produto_id)
    if db_produto:
        for key, value in produto.dict(exclude_unset=True).items():
            setattr(db_produto, key, value)
        db.commit()
        db.refresh(db_produto)
    return db_produto

def deletar_produto(db: Session, produto_id: int):
    db_produto = obter_produto(db, produto_id)
    if db_produto:
        db.delete(db_produto)
        db.commit()
    return db_produto
