from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from datetime import date
from enum import Enum

from app.produtos.schemas import ProdutoResponse, ProdutoPedidoResponse
from app.pedidos.models import StatusPedido

class OrdenarPor(str, Enum):
    criado_em = "criado_em"
    total = "total"
    status = "status"

class Direcao(str, Enum):
    desc = "desc"
    asc = "asc"


class ItensResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    qtd_produto: int
    valor_unitario: Decimal
    produto: ProdutoResponse

class PedidoResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    valor_total: Decimal
    status: StatusPedido
    itens: list[ItensResponse]

class PedidoCreate(BaseModel):
    produtos: list[ProdutoPedidoResponse]

class PedidosFilters(BaseModel):
    limit: int = Field(ge=1, default=10, le=100)
    offset: int = Field(ge=0, default=0)
    ordenar_por: OrdenarPor = OrdenarPor.criado_em
    direcao: Direcao = Direcao.desc
    status: StatusPedido | None = None
    id_funcionario: int | None = Field(ge=1, default=None)
    sem_funcionario: bool | None = None
    id_usuario: int | None = Field(ge=1, default=None)
    dt_inicio: date | None = None
    dt_fim: date | None = None
