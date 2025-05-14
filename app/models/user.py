import uuid
from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False) # Added for potential admin roles
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Add other fields as needed, for example:
    # first_name = Column(String, index=True)
    # last_name = Column(String, index=True)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', is_active={self.is_active})>"

# Como criar novas migrações (já mencionado em main.py, mas reforçando aqui):
# 1. Certifique-se de que seus modelos de banco de dados (como este arquivo) estão atualizados.
# 2. Execute o comando: `alembic revision -m "sua_mensagem_de_migracao"`
#    Isso gerará um novo script de migração em alembic/versions/.
# 3. Edite o script gerado para definir as operações de upgrade e downgrade.
#    Use as funções do SQLAlchemy e Alembic op (por exemplo, op.create_table(), op.add_column()).
# 4. Aplique a migração: `alembic upgrade head`

# Exemplo de tabela para refresh tokens (pode ser em um arquivo separado como app/models/token.py)
# class RefreshToken(Base):
#     __tablename__ = "refresh_tokens"
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
#     token = Column(String, unique=True, index=True, nullable=False)
#     expires_at = Column(DateTime, nullable=False)
#     created_at = Column(DateTime, default=func.now())
#     user = relationship("User")

