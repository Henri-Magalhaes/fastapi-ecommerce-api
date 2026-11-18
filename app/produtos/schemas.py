from pydantic import BaseModel, ConfigDict, Field, model_validator
from decimal import Decimal

from app.autenticacao.schemas import StringNaoVazia
from app.categorias.schemas import CategoriaResponse, NomeCategoriaNormalizado

class ProdutoResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    nome: str
    categoria: CategoriaResponse

class ProdutoPaginated(BaseModel):
    limit: int = Field(ge=1, le=100, default=15)
    offset: int = Field(ge=0, default=0)
    categoria: NomeCategoriaNormalizado | None = None

class ProdutoCreate(BaseModel):
    nome: StringNaoVazia = Field(max_length=50)
    id_categoria: int = Field(ge=1)
    valor_unitario: Decimal = Field(ge=0, decimal_places=2, max_digits=8)
    estoque: int = Field(ge=0, le=1000000)

class ProdutoUpdate(BaseModel):
    nome: StringNaoVazia | None = Field(default=None, max_length=50)
    id_categoria: int | None = Field(default=None, ge=1)
    valor_unitario: Decimal | None = Field(default=None, ge=0, decimal_places=2, max_digits=8)

    @model_validator(mode="before")
    @classmethod
    def validar_dados(cls, data):
        if isinstance(data, dict):
            for campo, valor in data.items():
                if valor is None:
                    raise ValueError(
                        f"O campo {campo} não pode ser nulo"
                    )

        return data

class ProdutoEstoque(BaseModel):
    estoque: int = Field(ge=0, le=1000000)

class ProdutoPedidoResponse(BaseModel):
    id: int = Field(ge=1)
    quantidade: int = Field(ge=1, lt=100, default=1)

