from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, DataError
from fastapi import HTTPException
import traceback
from decimal import Decimal

from sqlalchemy.orm import relationship, joinedload

from app.models.pagamento import Pagamento, MetodoPagamento
from app.models import Cliente, User, Pedido, Venda
from app.models.comanda import Comanda, StatusComanda
from app.models.fiado import Fiado, StatusFiado
from app.schemas.pagamento_schemas import PagamentoCreateSchema, PagamentoUpdateSchema


# MODIFICAÇÃO: Função auxiliar atualizada para nova lógica onde valor_total_calculado é o saldo devedor restante
async def _calcular_valores_e_status_comanda(comanda: Comanda, db_session: AsyncSession):
    """
    Recalcula o status da comanda conforme nova lógica:
    - valor_final_comanda = apenas total dos itens
    - valor_total_calculado = saldo devedor restante (valor original - pagamentos)
    """

    # Recalcular valor da taxa de serviço baseado no total dos itens (valor_final_comanda)
    total_itens = comanda.valor_final_comanda or Decimal("0.00")
    percentual_taxa = comanda.percentual_taxa_servico or Decimal("0.00")
    comanda.valor_taxa_servico = (total_itens * percentual_taxa / Decimal("100.00")).quantize(Decimal("0.01"))

    # Calcular valor total original (antes dos pagamentos)
    desconto = comanda.valor_desconto or Decimal("0.00")
    valor_total_original = max(Decimal("0.00"), total_itens + comanda.valor_taxa_servico - desconto)

    # MODIFICAÇÃO: Atualizar o valor_total_calculado como saldo devedor restante
    valor_pago = comanda.valor_pago or Decimal("0.00")
    valor_fiado = comanda.valor_fiado or Decimal("0.00")
    valor_credito = comanda.valor_credito_usado or Decimal("0.00")

    comanda.valor_total_calculado = max(Decimal("0.00"),
                                        valor_total_original - valor_pago - valor_fiado - valor_credito)

    # Valor devido real (saldo devedor restante)
    valor_devido_real = comanda.valor_total_calculado
    # Valor total coberto por pagamentos diretos e fiado
    valor_total_coberto = comanda.valor_coberto
    # Valor pago diretamente (sem crédito usado, sem fiado)
    valor_pago_direto = comanda.valor_pago or Decimal("0.00")
    # Valor registrado como fiado
    valor_fiado_registrado = comanda.valor_fiado or Decimal("0.00")

    status_anterior = comanda.status_comanda
    novo_status = StatusComanda.ABERTA  # Default

    # MODIFICAÇÃO: Status baseado no saldo devedor restante (valor_total_calculado)
    if valor_devido_real <= Decimal("0.00"):  # Não há mais saldo devedor
        novo_status = StatusComanda.PAGA_TOTALMENTE
    # Condição para EM_FIADO: todo o valor coberto é igual ao valor fiado (e maior que zero)
    elif valor_total_coberto > Decimal("0.00") and valor_total_coberto == valor_fiado_registrado:
        novo_status = StatusComanda.EM_FIADO
    # Condição para PAGA_PARCIALMENTE: pagou/cobriu algo, mas ainda há saldo devedor
    elif valor_total_coberto > Decimal("0.00"):
        novo_status = StatusComanda.PAGA_PARCIALMENTE
    else:  # Nenhum valor coberto
        novo_status = StatusComanda.ABERTA

    comanda.status_comanda = novo_status
    return None


# --- Funções listar_pagamentos e obter_pagamento mantidas como antes ---
async def listar_pagamentos(db_session: AsyncSession, skip: int = 0, limit: int = 100):
    query = select(Pagamento).offset(skip).limit(limit)
    result = await db_session.execute(query)
    return result.scalars().all()


async def obter_pagamento(db_session: AsyncSession, pagamento_id: int):
    query = select(Pagamento).where(Pagamento.id == pagamento_id)
    result = await db_session.execute(query)
    return result.scalars().first()


async def criar_pagamento(db_session: AsyncSession, pagamento_data: PagamentoCreateSchema):
    # Validar existência da comanda (e carregar cliente associado se houver)
    comanda_query = select(Comanda).options(joinedload(Comanda.cliente)).where(Comanda.id == pagamento_data.id_comanda)
    comanda_result = await db_session.execute(comanda_query)
    comanda = comanda_result.scalars().first()
    if not comanda:
        raise HTTPException(status_code=400, detail=f"Comanda ID {pagamento_data.id_comanda} não encontrada.")

    # MODIFICAÇÃO: Validações da Comanda usando o saldo devedor restante (valor_total_calculado)
    saldo_devedor_atual = comanda.valor_total_calculado

    if saldo_devedor_atual <= Decimal("0.00"):
        pass  # A comanda já está paga, mas permite registrar pagamento

    # Validação específica para FIADO: id_cliente é obrigatório
    cliente_pagamento = None
    if pagamento_data.id_cliente:
        cliente_query = select(Cliente).where(Cliente.id == pagamento_data.id_cliente)
        cliente_result = await db_session.execute(cliente_query)
        cliente_pagamento = cliente_result.scalars().first()
        if not cliente_pagamento:
            raise HTTPException(status_code=400, detail=f"Cliente ID {pagamento_data.id_cliente} não encontrado.")
        if comanda.id_cliente_associado and comanda.id_cliente_associado != pagamento_data.id_cliente:
            raise HTTPException(status_code=400,
                                detail=f"O cliente do pagamento (ID {pagamento_data.id_cliente}) não corresponde ao cliente associado à comanda (ID {comanda.id_cliente_associado}).")
        # Se a comanda não tem cliente, associa o do pagamento
        if not comanda.id_cliente_associado:
            comanda.id_cliente_associado = pagamento_data.id_cliente
            comanda.cliente = cliente_pagamento

    if pagamento_data.metodo_pagamento == MetodoPagamento.FIADO and not comanda.id_cliente_associado:
        raise HTTPException(status_code=400, detail="ID do Cliente é obrigatório para pagamentos Fiado.")

    # Validação do usuário que registrou
    if pagamento_data.id_usuario_registrou:
        usuario_query = select(User).where(User.id == pagamento_data.id_usuario_registrou)
        usuario_result = await db_session.execute(usuario_query)
        if not usuario_result.scalars().first():
            raise HTTPException(status_code=400,
                                detail=f"Usuário ID {pagamento_data.id_usuario_registrou} não encontrado.")

    try:
        novo_pagamento = Pagamento(**pagamento_data.dict())
        if novo_pagamento.valor_pago <= Decimal("0.00"):
            raise HTTPException(status_code=400, detail="O valor do pagamento deve ser positivo.")
        db_session.add(novo_pagamento)

        # Atualizar Comanda
        valor_pagamento_atual = novo_pagamento.valor_pago
        novo_fiado_record = None

        # Adicionar ao valor_pago direto da comanda
        comanda.valor_pago = (comanda.valor_pago or Decimal("0.00")) + valor_pagamento_atual

        # Se for FIADO, também adicionar ao valor_fiado e criar registro Fiado
        if novo_pagamento.metodo_pagamento == MetodoPagamento.FIADO:
            comanda.valor_fiado = (comanda.valor_fiado or Decimal("0.00")) + valor_pagamento_atual
            # Criar registro Fiado
            novo_fiado_record = Fiado(
                id_comanda=comanda.id,
                id_cliente=comanda.id_cliente_associado,
                id_usuario_registrou=novo_pagamento.id_usuario_registrou,
                valor_original=valor_pagamento_atual,
                valor_devido=valor_pagamento_atual,
                status_fiado=StatusFiado.PENDENTE,
                observacoes=f"Fiado registrado via Pagamento ID: {novo_pagamento.id}"
            )
            db_session.add(novo_fiado_record)

        # MODIFICAÇÃO: Calcular status usando nova lógica onde valor_total_calculado é o saldo devedor restante
        cliente_com_saldo_atualizado = await _calcular_valores_e_status_comanda(comanda, db_session)
        db_session.add(comanda)
        if cliente_com_saldo_atualizado:
            db_session.add(cliente_com_saldo_atualizado)

        await db_session.flush()
        if novo_fiado_record:
            novo_fiado_record.observacoes = f"Fiado registrado via Pagamento ID: {novo_pagamento.id}"
            db_session.add(novo_fiado_record)

        await db_session.commit()
        await db_session.refresh(novo_pagamento)
        await db_session.refresh(comanda)
        if novo_fiado_record:
            await db_session.refresh(novo_fiado_record)

        return novo_pagamento
    except HTTPException as http_exc:
        await db_session.rollback()
        raise http_exc
    except (IntegrityError, DataError) as e:
        await db_session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro de banco de dados ao criar pagamento: {e}")
    except Exception as e:
        await db_session.rollback()
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao criar pagamento: {e}\n{error_trace}")


async def atualizar_pagamento(db_session: AsyncSession, pagamento_id: int, dados_update: PagamentoUpdateSchema):
    pagamento_db = await obter_pagamento(db_session, pagamento_id)
    if not pagamento_db:
        raise HTTPException(status_code=404, detail=f"Pagamento ID {pagamento_id} não encontrado.")

    # Carrega a comanda e o cliente associado (se houver)
    comanda_query = select(Comanda).options(relationship(Comanda.cliente)).where(Comanda.id == pagamento_db.id_comanda)
    comanda_result = await db_session.execute(comanda_query)
    comanda = comanda_result.scalars().first()
    if not comanda:
        raise HTTPException(status_code=500, detail="Erro crítico: Comanda associada ao pagamento não encontrada.")

    dados_dict = dados_update.dict(exclude_unset=True)
    if "id_comanda" in dados_dict and dados_dict["id_comanda"] != pagamento_db.id_comanda:
        raise HTTPException(status_code=400, detail="Alterar a comanda de um pagamento não é suportado.")

    try:
        # Valores antigos do pagamento
        valor_pago_antigo = pagamento_db.valor_pago
        metodo_antigo = pagamento_db.metodo_pagamento
        id_cliente_antigo_pagamento = pagamento_db.id_cliente

        # Novos valores (ou mantém os antigos se não fornecidos)
        valor_pago_novo = dados_dict.get("valor_pago", valor_pago_antigo)
        metodo_novo = dados_dict.get("metodo_pagamento", metodo_antigo)
        id_cliente_novo_pagamento = dados_dict.get("id_cliente", id_cliente_antigo_pagamento)

        # Validações dos novos dados
        if "valor_pago" in dados_dict and valor_pago_novo <= Decimal("0.00"):
            raise HTTPException(status_code=400, detail="O valor do pagamento deve ser positivo.")

        cliente_novo_obj = None
        if "id_cliente" in dados_dict or metodo_novo == MetodoPagamento.FIADO:
            if not id_cliente_novo_pagamento:
                raise HTTPException(status_code=400, detail="ID do Cliente é obrigatório para pagamentos Fiado.")
            cliente_query = select(Cliente).where(Cliente.id == id_cliente_novo_pagamento)
            cliente_result = await db_session.execute(cliente_query)
            cliente_novo_obj = cliente_result.scalars().first()
            if not cliente_novo_obj:
                raise HTTPException(status_code=400, detail=f"Cliente ID {id_cliente_novo_pagamento} não encontrado.")
            if comanda.id_cliente_associado and comanda.id_cliente_associado != id_cliente_novo_pagamento:
                raise HTTPException(status_code=400,
                                    detail=f"O novo cliente do pagamento não corresponde ao cliente da comanda.")
            if not comanda.id_cliente_associado:
                comanda.id_cliente_associado = id_cliente_novo_pagamento
                comanda.cliente = cliente_novo_obj

        if metodo_novo == MetodoPagamento.FIADO and not comanda.id_cliente_associado:
            raise HTTPException(status_code=400, detail="ID do Cliente é obrigatório para pagamentos Fiado.")

        # Determinar se precisa recalcular valores da comanda
        mudanca_valor = valor_pago_novo != valor_pago_antigo
        mudanca_metodo = metodo_novo != metodo_antigo
        mudanca_cliente_relevante = (id_cliente_novo_pagamento != id_cliente_antigo_pagamento) and (
                    metodo_novo == MetodoPagamento.FIADO or metodo_antigo == MetodoPagamento.FIADO)

        atualizar_valores_comanda = mudanca_valor or mudanca_metodo or mudanca_cliente_relevante
        fiado_record_para_deletar_stmt = None
        fiado_record_para_criar = None
        cliente_com_saldo_atualizado = None

        if atualizar_valores_comanda:
            # --- Reverter valor antigo da comanda ---
            comanda.valor_pago = (comanda.valor_pago or Decimal("0.00")) - valor_pago_antigo
            if metodo_antigo == MetodoPagamento.FIADO:
                comanda.valor_fiado = (comanda.valor_fiado or Decimal("0.00")) - valor_pago_antigo
                fiado_del_stmt = delete(Fiado).where(
                    Fiado.id_comanda == comanda.id,
                    Fiado.id_cliente == id_cliente_antigo_pagamento,
                    Fiado.valor_original == valor_pago_antigo,
                ).execution_options(synchronize_session=False)
                fiado_record_para_deletar_stmt = fiado_del_stmt

            # --- Aplicar valor novo na comanda ---
            comanda.valor_pago = (comanda.valor_pago or Decimal("0.00")) + valor_pago_novo
            if metodo_novo == MetodoPagamento.FIADO:
                comanda.valor_fiado = (comanda.valor_fiado or Decimal("0.00")) + valor_pago_novo
                fiado_record_para_criar = Fiado(
                    id_comanda=comanda.id,
                    id_cliente=comanda.id_cliente_associado,
                    id_usuario_registrou=dados_dict.get("id_usuario_registrou", pagamento_db.id_usuario_registrou),
                    valor_original=valor_pago_novo,
                    valor_devido=valor_pago_novo,
                    status_fiado=StatusFiado.PENDENTE,
                    observacoes=f"Fiado (re)registrado via atualização Pagamento ID: {pagamento_db.id}"
                )

            # Garantir não negatividade dos valores na comanda
            comanda.valor_fiado = max(Decimal("0.00"), comanda.valor_fiado or Decimal("0.00"))
            comanda.valor_pago = max(Decimal("0.00"), comanda.valor_pago or Decimal("0.00"))

            # MODIFICAÇÃO: Recalcular status usando nova lógica onde valor_total_calculado é o saldo devedor restante
            cliente_com_saldo_atualizado = await _calcular_valores_e_status_comanda(comanda, db_session)
            db_session.add(comanda)
            if cliente_com_saldo_atualizado:
                db_session.add(cliente_com_saldo_atualizado)

        # Atualizar os campos do próprio pagamento
        for key, value in dados_dict.items():
            setattr(pagamento_db, key, value)
        db_session.add(pagamento_db)

        # Executar delete e add do fiado se necessário
        if fiado_record_para_deletar_stmt is not None:
            await db_session.execute(fiado_record_para_deletar_stmt)
        if fiado_record_para_criar is not None:
            db_session.add(fiado_record_para_criar)

        await db_session.commit()
        await db_session.refresh(pagamento_db)
        if atualizar_valores_comanda:
            await db_session.refresh(comanda)

        return pagamento_db
    except HTTPException as http_exc:
        await db_session.rollback()
        raise http_exc
    except (IntegrityError, DataError) as e:
        await db_session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro de banco de dados ao atualizar pagamento: {e}")
    except Exception as e:
        await db_session.rollback()
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao atualizar pagamento: {e}\n{error_trace}")


async def deletar_pagamento(db_session: AsyncSession, pagamento_id: int):
    pagamento_db = await obter_pagamento(db_session, pagamento_id)
    if not pagamento_db:
        raise HTTPException(status_code=404, detail=f"Pagamento ID {pagamento_id} não encontrado.")

    # Carrega a comanda e o cliente associado (se houver)
    comanda_query = select(Comanda).options(relationship(Comanda.cliente)).where(Comanda.id == pagamento_db.id_comanda)
    comanda_result = await db_session.execute(comanda_query)
    comanda = comanda_result.scalars().first()
    if not comanda:
        print(
            f"Aviso: Comanda ID {pagamento_db.id_comanda} associada ao Pagamento ID {pagamento_id} não encontrada ao deletar.")
        await db_session.delete(pagamento_db)
        await db_session.commit()
        return {"message": f"Pagamento ID {pagamento_id} deletado, mas comanda associada não encontrada."}

    try:
        valor_pago_a_reverter = pagamento_db.valor_pago
        metodo_pagamento_reverter = pagamento_db.metodo_pagamento
        id_cliente_pagamento = pagamento_db.id_cliente

        fiado_record_para_deletar_stmt = None
        cliente_com_saldo_atualizado = None

        # --- Reverter valores na comanda ---
        comanda.valor_pago = (comanda.valor_pago or Decimal("0.00")) - valor_pago_a_reverter
        if metodo_pagamento_reverter == MetodoPagamento.FIADO:
            comanda.valor_fiado = (comanda.valor_fiado or Decimal("0.00")) - valor_pago_a_reverter
            fiado_del_stmt = delete(Fiado).where(
                Fiado.id_comanda == comanda.id,
                Fiado.id_cliente == id_cliente_pagamento,
                Fiado.valor_original == valor_pago_a_reverter,
            ).execution_options(synchronize_session=False)
            fiado_record_para_deletar_stmt = fiado_del_stmt

        # Garantir não negatividade
        comanda.valor_fiado = max(Decimal("0.00"), comanda.valor_fiado or Decimal("0.00"))
        comanda.valor_pago = max(Decimal("0.00"), comanda.valor_pago or Decimal("0.00"))

        # MODIFICAÇÃO: Recalcular status usando nova lógica onde valor_total_calculado é o saldo devedor restante
        cliente_com_saldo_atualizado = await _calcular_valores_e_status_comanda(comanda, db_session)
        db_session.add(comanda)
        if cliente_com_saldo_atualizado:
            db_session.add(cliente_com_saldo_atualizado)

        # Deletar o pagamento em si
        await db_session.delete(pagamento_db)

        # Executar delete do fiado se necessário
        if fiado_record_para_deletar_stmt is not None:
            await db_session.execute(fiado_record_para_deletar_stmt)

        await db_session.commit()

        return {"message": f"Pagamento ID {pagamento_id} deletado com sucesso e valores da comanda atualizados."}

    except HTTPException as http_exc:
        await db_session.rollback()
        raise http_exc
    except (IntegrityError, DataError) as e:
        await db_session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro de banco de dados ao deletar pagamento: {e}")
    except Exception as e:
        await db_session.rollback()
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao deletar pagamento: {e}\n{error_trace}")


# MODIFICAÇÃO: Função de aplicar crédito atualizada para nova lógica onde valor_total_calculado é o saldo devedor restante
async def aplicar_credito_cliente_na_comanda(db_session: AsyncSession, comanda_id: int, cliente_id: int):
    """Tenta aplicar o saldo de crédito de um cliente a uma comanda."""
    comanda_query = select(Comanda).where(Comanda.id == comanda_id)
    comanda_result = await db_session.execute(comanda_query)
    comanda = comanda_result.scalars().first()
    if not comanda:
        raise HTTPException(status_code=404, detail=f"Comanda ID {comanda_id} não encontrada.")

    cliente_query = select(Cliente).where(Cliente.id == cliente_id)
    cliente_result = await db_session.execute(cliente_query)
    cliente = cliente_result.scalars().first()
    if not cliente:
        raise HTTPException(status_code=404, detail=f"Cliente ID {cliente_id} não encontrado.")

    # MODIFICAÇÃO: Usar saldo devedor restante (valor_total_calculado)
    saldo_devedor_comanda = comanda.valor_total_calculado
    if saldo_devedor_comanda <= Decimal("0.00"):
        return {"message": "Comanda não possui saldo devedor.", "credito_aplicado": Decimal("0.00")}

    saldo_credito_cliente = cliente.saldo_credito or Decimal("0.00")
    if saldo_credito_cliente <= Decimal("0.00"):
        return {"message": "Cliente não possui saldo de crédito.", "credito_aplicado": Decimal("0.00")}

    # Determinar quanto crédito pode ser aplicado
    credito_a_aplicar = min(saldo_credito_cliente, saldo_devedor_comanda)

    if credito_a_aplicar <= Decimal("0.00"):
        return {"message": "Nenhum crédito a aplicar.", "credito_aplicado": Decimal("0.00")}

    try:
        # Aplicar o crédito
        comanda.valor_credito_usado = (comanda.valor_credito_usado or Decimal("0.00")) + credito_a_aplicar
        cliente.saldo_credito = saldo_credito_cliente - credito_a_aplicar

        # Associar cliente à comanda se ainda não estiver
        if not comanda.id_cliente_associado:
            comanda.id_cliente_associado = cliente.id
            comanda.cliente = cliente
        elif comanda.id_cliente_associado != cliente.id:
            await db_session.rollback()
            raise HTTPException(status_code=400,
                                detail="Erro: Tentativa de aplicar crédito de um cliente diferente do associado à comanda.")

        # MODIFICAÇÃO: Recalcular status da comanda usando nova lógica onde valor_total_calculado é o saldo devedor restante
        cliente_saldo_modificado = await _calcular_valores_e_status_comanda(comanda, db_session)

        db_session.add(comanda)
        db_session.add(cliente)
        await db_session.commit()
        await db_session.refresh(comanda)
        await db_session.refresh(cliente)

        return {
            "message": f"Crédito de {credito_a_aplicar:.2f} aplicado com sucesso.",
            "credito_aplicado": credito_a_aplicar,
            "novo_saldo_cliente": cliente.saldo_credito,
            "novo_status_comanda": comanda.status_comanda,
            "novo_saldo_devedor_comanda": comanda.valor_total_calculado
        }

    except Exception as e:
        await db_session.rollback()
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao aplicar crédito: {e}\n{error_trace}")
