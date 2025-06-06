import uuid
from sqlalchemy import Column, String, Boolean, DateTime, func, Integer
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)

    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, unique=True, nullable=True)
    imagem_url = Column(String(255), nullable=True, index=True)

    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relacionamentos
    vendas = relationship("Venda", back_populates="usuario")
    refresh_tokens = relationship("RefreshToken", back_populates="user")

    def __repr__(self):
        return (
            f"<User(id={self.id}, email='{self.email}', username='{self.username}', "
            f"is_active={self.is_active}, is_superuser={self.is_superuser})>"
        )
