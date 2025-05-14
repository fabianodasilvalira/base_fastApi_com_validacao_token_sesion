from sqlalchemy import Column, String, Integer, ForeignKey, Boolean # Adicionado Boolean
from sqlalchemy.orm import relationship
import enum
import uuid # Importar uuid para gerar hashes únicos
from sqlalchemy import Enum as SAEnum
from app.db.base import Base

class StatusMesa(str, enum.Enum):
    DISPONIVEL = "Disponível"
    OCUPADA = "Ocupada"
    RESERVADA = "Reservada"
    FECHADA = "Fechada"
    MANUTENCAO = "Manutenção" # Novo status sugerido

class Mesa(Base):
    __tablename__ = "mesas"

    id = Column(String, primary_key=True, index=True) # Considerar se ID deveria ser Integer autoincrementável
    numero_identificador = Column(String, nullable=False, unique=True, index=True)
    capacidade = Column(Integer, nullable=True)
    status = Column(SAEnum(StatusMesa), default=StatusMesa.DISPONIVEL, nullable=False)
    qr_code_hash = Column(String, nullable=True, unique=True, index=True) # Hash para acesso público (cardápio/chamar garçom)
    id_cliente_associado = Column(ForeignKey("clientes.id"), nullable=True)
    ativa_para_pedidos = Column(Boolean, default=True, nullable=False) # Novo campo para controlar se a mesa pode receber pedidos

    # Usando string para evitar importação circular
    cliente_associado = relationship("Cliente", back_populates="mesas_associadas")
    comandas = relationship("Comanda", back_populates="mesa")
    pedidos = relationship("Pedido", back_populates="mesa")

    # # Método para gerar QR Code hash se não existir, pode ser chamado no service ao criar/habilitar mesa para QR
    # def gerar_qr_code_hash(self, force_new=False):
    #     if not self.qr_code_hash or force_new:
    #         self.qr_code_hash = str(uuid.uuid4())

