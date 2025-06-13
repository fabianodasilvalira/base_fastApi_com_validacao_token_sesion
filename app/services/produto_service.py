from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List
from collections import defaultdict

from app.models.produto import Produto
from app.models.categoria import Categoria
from app.schemas.produto_schemas import ProdutoCreate, ProdutoUpdate, CategoriaComProdutosOut
from fastapi import HTTPException


async def criar_produto(db: AsyncSession, produto: ProdutoCreate) -> Produto:
    """Cria um novo produto."""
    # Verifica se a categoria existe, se foi fornecida
    if produto.categoria_id:
        categoria = await _verificar_categoria_existe(db, produto.categoria_id)
        if not categoria:
            raise HTTPException(status_code=400, detail="Categoria não encontrada")

    try:
        # Corrige a sequência antes de inserir
        await _corrigir_sequencia_produtos(db)

        # Cria o produto sem especificar o ID (deixa o autoincrement funcionar)
        produto_data = produto.dict()
        if 'id' in produto_data:
            del produto_data['id']  # Remove ID se existir

        db_produto = Produto(**produto_data)
        db.add(db_produto)
        await db.commit()
        await db.refresh(db_produto)
        return db_produto
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar produto: {str(e)}")


async def listar_produtos(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Produto]:
    """Lista produtos com paginação."""
    stmt = (
        select(Produto)
        .options(selectinload(Produto.categoria_relacionada))
        .offset(skip)
        .limit(limit)
        .order_by(Produto.id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def listar_cardapio(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[CategoriaComProdutosOut]:
    """Lista produtos agrupados por categoria para cardápio."""
    # Busca produtos com categoria carregada
    stmt = (
        select(Produto)
        .options(selectinload(Produto.categoria_relacionada))
        .where(Produto.disponivel == True)
        .offset(skip)
        .limit(limit)
        .order_by(Produto.categoria_id, Produto.nome)
    )
    result = await db.execute(stmt)
    produtos = result.scalars().all()

    # Agrupa produtos por categoria
    agrupados = defaultdict(list)
    for produto in produtos:
        categoria_nome = produto.categoria_relacionada.nome if produto.categoria_relacionada else "Sem Categoria"
        agrupados[categoria_nome].append(produto)

    # Converte para o schema de resposta
    resultado = [
        CategoriaComProdutosOut(categoria=categoria, produtos=produtos_lista)
        for categoria, produtos_lista in agrupados.items()
    ]

    return resultado


async def obter_produto(db: AsyncSession, produto_id: int) -> Produto | None:
    """Obtém um produto por ID, incluindo categoria relacionada."""
    stmt = (
        select(Produto)
        .options(selectinload(Produto.categoria_relacionada))  # Carrega a relação
        .where(Produto.id == produto_id)
    )
    result = await db.execute(stmt)
    produto = result.scalar_one_or_none()  # Retorna a instância ORM do Produto ou None
    return produto


async def atualizar_produto(db: AsyncSession, produto_id: int, produto: ProdutoUpdate) -> Produto:
    """Atualiza um produto existente."""
    db_produto = await obter_produto(db, produto_id)
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    # Verifica se a categoria existe, se foi fornecida no update
    if produto.categoria_id is not None:
        categoria = await _verificar_categoria_existe(db, produto.categoria_id)
        if not categoria:
            raise HTTPException(status_code=400, detail="Categoria não encontrada")

    try:
        update_data = produto.dict(exclude_unset=True)
        # Remove ID do update se existir
        if 'id' in update_data:
            del update_data['id']

        for key, value in update_data.items():
            setattr(db_produto, key, value)

        await db.commit()
        await db.refresh(db_produto)
        return db_produto

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar produto: {str(e)}")


async def deletar_produto(db: AsyncSession, produto_id: int) -> Produto:
    """Deleta um produto."""
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


async def listar_produtos_por_categoria(db: AsyncSession, categoria_id: int, skip: int = 0, limit: int = 100) -> List[
    Produto]:
    """Lista produtos de uma categoria específica."""
    # Verifica se a categoria existe
    categoria = await _verificar_categoria_existe(db, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    stmt = (
        select(Produto)
        .options(selectinload(Produto.categoria_relacionada))
        .where(Produto.categoria_id == categoria_id)
        .offset(skip)
        .limit(limit)
        .order_by(Produto.nome)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def _verificar_categoria_existe(db: AsyncSession, categoria_id: int) -> bool:
    """Função auxiliar para verificar se uma categoria existe."""
    stmt = select(Categoria).where(Categoria.id == categoria_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def _corrigir_sequencia_produtos(db: AsyncSession):
    """Corrige a sequência de IDs da tabela produtos."""
    try:
        # Obtém o próximo valor da sequência baseado no maior ID existente
        query = text("""
            SELECT setval('produtos_id_seq', 
                COALESCE((SELECT MAX(id) FROM produtos), 0) + 1, 
                false
            );
        """)
        await db.execute(query)
        await db.commit()
    except Exception as e:
        await db.rollback()
        # Se der erro, não falha a operação principal
        print(f"Aviso: Não foi possível corrigir a sequência: {e}")


async def resetar_sequencia_produtos(db: AsyncSession):
    """Função utilitária para resetar completamente a sequência (use com cuidado)."""
    try:
        query = text("""
            SELECT setval('produtos_id_seq', 
                COALESCE((SELECT MAX(id) FROM produtos), 0) + 1
            );
        """)
        await db.execute(query)
        await db.commit()
        return {"message": "Sequência resetada com sucesso"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao resetar sequência: {str(e)}")
