from sqlalchemy.orm import Session
from app.models.categoria import Categoria
from app.schemas.categoria_schemas import CategoriaCreate, CategoriaUpdate

def get_all(db: Session):
    return db.query(Categoria).all()

def get_by_id(db: Session, categoria_id: int):
    return db.query(Categoria).filter(Categoria.id == categoria_id).first()

def create(db: Session, categoria: CategoriaCreate):
    db_categoria = Categoria(**categoria.dict())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

def update(db: Session, categoria_id: int, categoria_update: CategoriaUpdate):
    db_categoria = get_by_id(db, categoria_id)
    if not db_categoria:
        return None
    for key, value in categoria_update.dict(exclude_unset=True).items():
        setattr(db_categoria, key, value)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

def delete(db: Session, categoria_id: int):
    db_categoria = get_by_id(db, categoria_id)
    if not db_categoria:
        return False
    db.delete(db_categoria)
    db.commit()
    return True
