import uuid
from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Assuming User.Base is the declarative_base() instance used across models.
# If you have a central Base, import it from there e.g., from .base import Base
from app.models.user import Base # Or from .base import Base if you create one

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User") # Defines the relationship to the User model

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"

# Onde modificar este modelo:
# - Adicione ou remova campos conforme necessário para os refresh tokens.
# - Se você alterar este modelo, lembre-se de gerar uma nova migração do Alembic:
#   `alembic revision -m "update_refresh_tokens_table" --autogenerate`
#   E depois aplique-a: `alembic upgrade head`

