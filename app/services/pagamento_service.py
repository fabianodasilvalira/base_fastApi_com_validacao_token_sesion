# app/services/pagamento_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, DataError
from fastapi import HTTPException
import traceback

from app.models.pagamento import Pagamento
from app.models import Cliente, Comanda, User, Pedido, Venda
from app.schemas.pagamento_schemas import PagamentoCreateSchema, PagamentoUpdateSchema


async def listar_pagamentos(db_session: AsyncSession, skip: int = 0, limit: int = 100):
    query = select(Pagamento).offset(skip).limit(limit)
    result = await db_session.execute(query)
    return result.scalars().all()


async def obter_pagamento(db_session: AsyncSession, pagamento_id: int):
    query = select(Pagamento).where(Pagamento.id == pagamento_id)
    result = await db_session.execute(query)
    return result.scalars().first()


async def criar_pagamento(db_session: AsyncSession, pagamento: PagamentoCreateSchema):
    # Validar existência da comanda (obrigatório)
    comanda_query = select(Comanda).where(Comanda.id == pagamento.id_comanda)
    comanda_result = await db_session.execute(comanda_query)
    comanda = comanda_result.scalars().first()
    if not comanda:
        raise HTTPException(
            status_code=400,
            detail=f"Comanda com ID {pagamento.id_comanda} não encontrada no banco de dados"
        )

    # Validar existência do cliente (opcional)
    if pagamento.id_cliente:
        cliente_query = select(Cliente).where(Cliente.id == pagamento.id_cliente)
        cliente_result = await db_session.execute(cliente_query)
        cliente = cliente_result.scalars().first()
        if not cliente:
            raise HTTPException(
                status_code=400,
                detail=f"Cliente com ID {pagamento.id_cliente} não encontrado no banco de dados"
            )

    # Validar existência do usuário (opcional)
    if pagamento.id_usuario_registrou:
        usuario_query = select(User).where(User.id == pagamento.id_usuario_registrou)
        usuario_result = await db_session.execute(usuario_query)
        usuario = usuario_result.scalars().first()
        if not usuario:
            raise HTTPException(
                status_code=400,
                detail=f"Usuário com ID {pagamento.id_usuario_registrou} não encontrado no banco de dados"
            )

    # Validar existência do pedido (opcional)
    if pagamento.id_pedido:
        pedido_query = select(Pedido).where(Pedido.id == pagamento.id_pedido)
        pedido_result = await db_session.execute(pedido_query)
        pedido = pedido_result.scalars().first()
        if not pedido:
            raise HTTPException(
                status_code=400,
                detail=f"Pedido com ID {pagamento.id_pedido} não encontrado no banco de dados"
            )

    # Validar existência da venda (opcional)
    if pagamento.id_venda:
        venda_query = select(Venda).where(Venda.id == pagamento.id_venda)
        venda_result = await db_session.execute(venda_query)
        venda = venda_result.scalars().first()
        if not venda:
            raise HTTPException(
                status_code=400,
                detail=f"Venda com ID {pagamento.id_venda} não encontrada no banco de dados"
            )

    try:
        novo_pagamento = Pagamento(**pagamento.dict())
        db_session.add(novo_pagamento)
        await db_session.commit()
        await db_session.refresh(novo_pagamento)
        return novo_pagamento
    except IntegrityError as e:
        await db_session.rollback()
        error_detail = str(e)
        if "foreign key constraint" in error_detail.lower():
            # Extrair informações mais detalhadas sobre a violação de chave estrangeira
            constraint_name = error_detail.split("constraint")[1].split("(")[
                0].strip() if "constraint" in error_detail else ""
            raise HTTPException(
                status_code=400,
                detail=f"Erro de integridade referencial: Violação da restrição {constraint_name}. Um dos IDs fornecidos não existe no banco de dados."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Erro de integridade ao criar pagamento: {error_detail}"
            )
    except DataError as e:
        await db_session.rollback()
        error_detail = str(e)
        if "invalid input" in error_detail.lower():
            # Extrair informações mais detalhadas sobre o erro de tipo de dados
            column_info = error_detail.split("for")[1].split(":")[0].strip() if "for" in error_detail else ""
            raise HTTPException(
                status_code=400,
                detail=f"Erro de tipo de dados: Valor inválido {column_info}. Verifique se o tipo de dados está correto."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Erro de dados ao criar pagamento: {error_detail}"
            )
    except Exception as e:
        await db_session.rollback()
        error_detail = str(e)
        error_trace = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar pagamento: {error_detail}\nDetalhes técnicos: {error_trace}"
        )


async def atualizar_pagamento(db_session: AsyncSession, pagamento_id: int, dados: PagamentoUpdateSchema):
    # Verificar se o pagamento existe
    pagamento_db = await obter_pagamento(db_session, pagamento_id)
    if not pagamento_db:
        raise HTTPException(
            status_code=404,
            detail=f"Pagamento com ID {pagamento_id} não encontrado no banco de dados"
        )

    # Validar existência da comanda (se fornecido)
    if dados.id_comanda:
        comanda_query = select(Comanda).where(Comanda.id == dados.id_comanda)
        comanda_result = await db_session.execute(comanda_query)
        comanda = comanda_result.scalars().first()
        if not comanda:
            raise HTTPException(
                status_code=400,
                detail=f"Comanda com ID {dados.id_comanda} não encontrada no banco de dados"
            )

    # Validar existência do cliente (opcional)
    if dados.id_cliente:
        cliente_query = select(Cliente).where(Cliente.id == dados.id_cliente)
        cliente_result = await db_session.execute(cliente_query)
        cliente = cliente_result.scalars().first()
        if not cliente:
            raise HTTPException(
                status_code=400,
                detail=f"Cliente com ID {dados.id_cliente} não encontrado no banco de dados"
            )

    # Validar existência do usuário (opcional)
    if dados.id_usuario_registrou:
        usuario_query = select(User).where(User.id == dados.id_usuario_registrou)
        usuario_result = await db_session.execute(usuario_query)
        usuario = usuario_result.scalars().first()
        if not usuario:
            raise HTTPException(
                status_code=400,
                detail=f"Usuário com ID {dados.id_usuario_registrou} não encontrado no banco de dados"
            )

    # Validar existência do pedido (opcional)
    if dados.id_pedido:
        pedido_query = select(Pedido).where(Pedido.id == dados.id_pedido)
        pedido_result = await db_session.execute(pedido_query)
        pedido = pedido_result.scalars().first()
        if not pedido:
            raise HTTPException(
                status_code=400,
                detail=f"Pedido com ID {dados.id_pedido} não encontrado no banco de dados"
            )

    # Validar existência da venda (opcional)
    if dados.id_venda:
        venda_query = select(Venda).where(Venda.id == dados.id_venda)
        venda_result = await db_session.execute(venda_query)
        venda = venda_result.scalars().first()
        if not venda:
            raise HTTPException(
                status_code=400,
                detail=f"Venda com ID {dados.id_venda} não encontrada no banco de dados"
            )

    try:
        # Atualizar apenas os campos fornecidos
        for key, value in dados.dict(exclude_unset=True).items():
            setattr(pagamento_db, key, value)

        db_session.add(pagamento_db)
        await db_session.commit()
        await db_session.refresh(pagamento_db)
        return pagamento_db
    except IntegrityError as e:
        await db_session.rollback()
        error_detail = str(e)
        if "foreign key constraint" in error_detail.lower():
            # Extrair informações mais detalhadas sobre a violação de chave estrangeira
            constraint_name = error_detail.split("constraint")[1].split("(")[
                0].strip() if "constraint" in error_detail else ""
            raise HTTPException(
                status_code=400,
                detail=f"Erro de integridade referencial: Violação da restrição {constraint_name}. Um dos IDs fornecidos não existe no banco de dados."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Erro de integridade ao atualizar pagamento: {error_detail}"
            )
    except DataError as e:
        await db_session.rollback()
        error_detail = str(e)
        if "invalid input" in error_detail.lower():
            # Extrair informações mais detalhadas sobre o erro de tipo de dados
            column_info = error_detail.split("for")[1].split(":")[0].strip() if "for" in error_detail else ""
            raise HTTPException(
                status_code=400,
                detail=f"Erro de tipo de dados: Valor inválido {column_info}. Verifique se o tipo de dados está correto."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Erro de dados ao atualizar pagamento: {error_detail}"
            )
    except Exception as e:
        await db_session.rollback()
        error_detail = str(e)
        error_trace = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar pagamento: {error_detail}\nDetalhes técnicos: {error_trace}"
        )


async def deletar_pagamento(db_session: AsyncSession, pagamento_id: int):
    # Verificar se o pagamento existe
    pagamento_db = await obter_pagamento(db_session, pagamento_id)
    if not pagamento_db:
        raise HTTPException(
            status_code=404,
            detail=f"Pagamento com ID {pagamento_id} não encontrado no banco de dados"
        )

    try:
        await db_session.delete(pagamento_db)
        await db_session.commit()
        return pagamento_db
    except IntegrityError as e:
        await db_session.rollback()
        error_detail = str(e)
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível excluir este pagamento pois ele possui registros associados: {error_detail}"
        )
    except Exception as e:
        await db_session.rollback()
        error_detail = str(e)
        error_trace = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao excluir pagamento: {error_detail}\nDetalhes técnicos: {error_trace}"
        )
