from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.models.categoria import Categoria
from app.schemas.categoria_schemas import CategoriaCreate, CategoriaUpdate


async def get_all(db: AsyncSession):
    result = await db.execute(select(Categoria).order_by(Categoria.nome))
    return result.scalars().all()


async def get_by_id(db: AsyncSession, categoria_id: int):
    result = await db.execute(
        select(Categoria)
        .where(Categoria.id == categoria_id)
        .options(selectinload(Categoria.produtos))
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, categoria: CategoriaCreate):
    # Convertemos o modelo Pydantic para dict e usamos diretamente
    db_categoria = Categoria(**categoria.model_dump())
    db.add(db_categoria)
    await db.commit()
    await db.refresh(db_categoria)
    return db_categoria


async def update(db: AsyncSession, categoria_id: int, categoria_update: CategoriaUpdate):
    # Primeiro buscamos a categoria existente
    db_categoria = await get_by_id(db, categoria_id)
    if not db_categoria:
        return None

    # Atualizamos os campos
    update_data = categoria_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_categoria, key, value)

    db.add(db_categoria)
    await db.commit()
    await db.refresh(db_categoria)
    return db_categoria


async def delete(db: AsyncSession, categoria_id: int):
    # Primeiro buscamos a categoria existente
    db_categoria = await get_by_id(db, categoria_id)
    if not db_categoria:
        return False

    # Removemos a categoria
    await db.delete(db_categoria)
    await db.commit()
    return True