from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class CategoriaBase(BaseModel):
    nome: str = Field(..., max_length=100, example="Eletrônicos")
    descricao: Optional[str] = Field(
        None,
        max_length=500,
        example="Produtos eletrônicos em geral"
    )
    imagem_url: Optional[str] = Field(
        None,
        max_length=255,
        example="https://exemplo.com/imagem.jpg"
    )

    @validator('imagem_url')
    def validate_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URL deve começar com http:// ou https://')
        return v

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaUpdate(CategoriaBase):
    pass

class CategoriaResponse(CategoriaBase):
    id: int
    criado_em: datetime
    atualizado_em: Optional[datetime]
    produtos_count: Optional[int] = Field(
        None,
        description="Quantidade de produtos nesta categoria",
        example=5
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "nome": "Eletrônicos",
                "descricao": "Produtos eletrônicos em geral",
                "imagem_url": "https://exemplo.com/imagem.jpg",
                "criado_em": "2023-01-01T00:00:00",
                "atualizado_em": "2023-01-02T00:00:00",
                "produtos_count": 5
            }
        }