from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.produto import Produto
from app.schemas.produto_schemas import ProdutoCreate, ProdutoUpdate
from fastapi import HTTPException
from app.models import Categoria


async def criar_produto(db: AsyncSession, produto: ProdutoCreate):
    try:
        db_produto = Produto(**produto.dict())
        db.add(db_produto)
        await db.commit()
        await db.refresh(db_produto)
        return db_produto
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar produto: {str(e)}")


async def listar_produtos(db: AsyncSession, skip: int = 0, limit: int = 100):
    stmt = select(Produto).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def obter_produto(db: AsyncSession, produto_id: int):
    stmt = select(Produto).where(Produto.id == produto_id)
    result = await db.execute(stmt)
    produto = result.scalar_one_or_none()
    return produto


async def atualizar_produto(db: AsyncSession, produto_id: int, produto: ProdutoUpdate):
    db_produto = await obter_produto(db, produto_id)
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    # ✅ Verifica se a categoria_id existe, se foi enviada no update
    if produto.categoria_id is not None:
        categoria = await db.execute(select(Categoria).filter(Categoria.id == produto.categoria_id))
        categoria_result = categoria.scalar_one_or_none()
        if not categoria_result:
            raise HTTPException(status_code=400, detail="Categoria não encontrada")

    try:
        update_data = produto.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_produto, key, value)

        await db.commit()
        await db.refresh(db_produto)
        return db_produto

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar produto: {str(e)}")


async def deletar_produto(db: AsyncSession, produto_id: int):
    db_produto = await obter_produto(db, produto_id)
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    try:
        await db.delete(db_produto)
        await db.commit()
        return db_produto
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao deletar produto: {str(e)}")


async def listar_produtos_por_categoria(db: AsyncSession, categoria_id: int, skip: int = 0, limit: int = 100):
    stmt = select(Produto).where(Produto.categoria_id == categoria_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
