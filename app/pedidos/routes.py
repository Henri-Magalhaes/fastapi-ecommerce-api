from typing import Annotated
from fastapi import APIRouter, Depends, Query, Path, Body
from http import HTTPStatus
from sqlalchemy.orm import Session

from app.core.models_registry import Usuario
from app.pedidos.models import StatusPedido
from app.core.dependencies import get_user, get_db, require_funcionario
from app.pedidos.services import PedidosService
from app.core.schemas import ApiResponse
from app.pedidos.schemas import PedidoResponse, PedidoCreate, PedidosFilters

order_router = APIRouter(
    prefix="/orders",
    tags=["Pedidos"]
)

@order_router.post("/", response_model=ApiResponse[PedidoResponse], status_code=HTTPStatus.CREATED)
async def criar_pedido(
    dados: PedidoCreate,
    cliente_atual: Usuario=Depends(get_user),
    session: Session=Depends(get_db)
):
    return PedidosService(session).criar_pedido(
        cliente_atual,
        dados
    )

@order_router.get("/", response_model=ApiResponse[list[PedidoResponse]])
async def mostrar_historico_pedidos(
    dados: Annotated[PedidosFilters, Query()],
    user_atual: Usuario=Depends(get_user),
    session: Session=Depends(get_db)
):
    return PedidosService(session).mostrar_pedidos(
        user_atual,
        dados
    )

@order_router.get("/{id_pedido}", response_model=ApiResponse[PedidoResponse])
async def buscar_pedido_por_id(
    id_pedido: Annotated[int, Path(ge=1)],
    user_atual: Usuario=Depends(get_user),
    session: Session=Depends(get_db)
):
    return PedidosService(session).buscar_pedido_por_id(
        user_atual,
        id_pedido
    )

@order_router.patch("/{id_pedido}/status", response_model=ApiResponse[PedidoResponse])
async def alterar_status_pedido(
    id_pedido: Annotated[int, Path(ge=1)],
    status: Annotated[StatusPedido, Body(embed=True)],
    atual_func: Usuario=Depends(require_funcionario),
    session: Session=Depends(get_db)
):
    return PedidosService(session).alterar_status(
        id_pedido,
        status
    )

@order_router.patch("/{id_pedido}/cancelar", response_model=ApiResponse[PedidoResponse])
async def cancelar_pedido(
    id_pedido: Annotated[int, Path(ge=1)],
    user_atual: Usuario=Depends(get_user),
    session: Session=Depends(get_db)
):
    return PedidosService(session).cancelar_pedido(
        id_pedido,
        user_atual
    )

@order_router.patch("/{id_pedido}/funcionario", response_model=ApiResponse[PedidoResponse])
async def atribuir_funcionario_pedido(
    id_pedido: Annotated[int, Path(ge=1)],
    id_func: Annotated[int, Body(ge=1, embed=True)],
    func_atual: Usuario=Depends(require_funcionario),
    session: Session=Depends(get_db)
):
    return PedidosService(session).atribuir_func(
        id_pedido,
        func_atual,
        id_func
    )