from sqlalchemy.orm import Session
from app.models.venda_produto_item import VendaProdutoItem
from app.schemas.venda_produto_item import VendaProdutoItemCreate, VendaProdutoItemUpdate


def create_item(db: Session, item: VendaProdutoItemCreate):
    db_item = VendaProdutoItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_itens_by_venda(db: Session, venda_id: int):
    return db.query(VendaProdutoItem).filter(VendaProdutoItem.id_venda == venda_id).all()


def update_item(db: Session, venda_id: int, produto_id: int, update_data: VendaProdutoItemUpdate):
    db_item = db.query(VendaProdutoItem).filter_by(id_venda=venda_id, id_produto=produto_id).first()
    if db_item:
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(db_item, field, value)
        db.commit()
        db.refresh(db_item)
    return db_item


def delete_item(db: Session, venda_id: int, produto_id: int):
    db_item = db.query(VendaProdutoItem).filter_by(id_venda=venda_id, id_produto=produto_id).first()
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item
