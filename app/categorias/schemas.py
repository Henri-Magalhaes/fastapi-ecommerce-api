from typing import Annotated
from fastapi import HTTPException
from http import HTTPStatus
from pydantic import BaseModel, ConfigDict, Field, AfterValidator

from app.autenticacao.schemas import StringNaoVazia

def normalizar_nome_categoria(valor: str):
    return valor.strip().upper()

NomeCategoriaNormalizado = Annotated[
    StringNaoVazia,
    AfterValidator(normalizar_nome_categoria)
]

class CategoriaResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    nome: StringNaoVazia

class CategoriaFilter(BaseModel):
    limit: int = Field(ge=1, le=100, default=10)
    offset: int = Field(ge=0, default=0)

class CategoriaCreate(BaseModel):
    nome: NomeCategoriaNormalizado = Field(max_length=50)