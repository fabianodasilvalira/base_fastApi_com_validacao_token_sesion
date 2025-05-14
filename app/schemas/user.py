from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

# --- User Schemas ---

# Base properties shared by other schemas
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    # Add other common fields here, e.g.:
    # first_name: Optional[str] = None
    # last_name: Optional[str] = None

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str = Field(..., min_length=8) # Ensure password has a minimum length
    # confirm_password: str # Optional: if you want password confirmation
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = Field(None, min_length=8) # Password is optional on update
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

# Properties stored in DB (inherits from UserBase, adds id and hashed_password)
# This schema is not directly exposed via API but used internally or for ORM mapping.
class UserInDBBase(UserBase):
    id: UUID
    hashed_password: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Pydantic V2 way to enable ORM mode

# Additional properties to return via API (public representation of a user)
class UserPublic(UserBase):
    id: UUID
    email: EmailStr # Email is not optional in public representation
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Pydantic V2 way to enable ORM mode

# Onde modificar Schemas de Usuário:
# - `UserBase`: Campos comuns a todas as variações do schema de usuário.
# - `UserCreate`: Campos esperados ao criar um novo usuário (ex: via endpoint de signup ou admin).
#   Inclui validações como `min_length` para a senha.
# - `UserUpdate`: Campos que podem ser atualizados para um usuário existente.
#   Todos os campos são opcionais.
# - `UserInDBBase`: Representa o usuário como armazenado no banco de dados, incluindo `id` e `hashed_password`.
#   Geralmente não é exposto diretamente pela API.
# - `UserPublic`: A representação pública de um usuário, retornada por endpoints da API.
#   Exclui campos sensíveis como `hashed_password`.

# Como usar estes schemas:
# - Em endpoints da API, use `UserCreate` para o corpo da requisição de criação,
#   `UserUpdate` para atualização, e `UserPublic` como `response_model`.
# - Internamente, `UserInDBBase` pode ser usado para type hinting de objetos de usuário
#   retornados pelo ORM.

