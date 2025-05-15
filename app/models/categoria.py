from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String, unique=True, nullable=False, index=True)
    descricao = Column(Text, nullable=True)
    imagem_url = Column(String(255), nullable=True, index=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    # Um-para-muitos: uma categoria pode ter muitos produtos
    produtos = relationship("Produto", back_populates="categoria_relacionada")
