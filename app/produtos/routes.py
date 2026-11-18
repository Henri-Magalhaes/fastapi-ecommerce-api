from typing import Annotated
from fastapi import APIRouter, Depends, Query, Path
from http import HTTPStatus

from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_user, require_funcionario
from app.core.schemas import ApiResponse
from app.produtos.schemas import ProdutoResponse, ProdutoPaginated, ProdutoCreate, ProdutoUpdate, ProdutoEstoque
from app.produtos.services import ProdutoService
from app.users.models import Usuario

product_router = APIRouter(
    prefix="/products",
    tags=["Produtos"]
)

@product_router.get("/", response_model=ApiResponse[list[ProdutoResponse]])
async def listagem_produtos(
    dados: Annotated[ProdutoPaginated, Query()],
    session: Session=Depends(get_db)
):
    return ProdutoService(session).listar_produtos(
        dados
    )

@product_router.get("/{produto_id}", response_model=ApiResponse[ProdutoResponse | None])
async def buscar_por_produto(
    produto_id: Annotated[int, Path(ge=1)],
    session: Session=Depends(get_db)
):
    return ProdutoService(session).buscar_produto_por_id(
        produto_id
    )

@product_router.post("/", status_code=HTTPStatus.CREATED, response_model=ApiResponse[ProdutoResponse])
async def adicionar_novo_produto(
    dados: ProdutoCreate,
    user_atual: Usuario=Depends(require_funcionario),
    session: Session=Depends(get_db)
):
    return ProdutoService(session).criar_produto(
        dados
    )

@product_router.patch("/{produto_id}", response_model=ApiResponse[ProdutoResponse])
async def atualizar_dados_produto(
    produto_id: Annotated[int, Path(ge=1)],
    dados: ProdutoUpdate,
    user_atual: Usuario=Depends(require_funcionario),
    session: Session=Depends(get_db)
):
    return ProdutoService(session).atualizar_produtos(
        produto_id,
        dados
    )

@product_router.patch("/{produto_id}/estoque", response_model=ApiResponse[ProdutoResponse])
async def ajustar_estoque_produto(
    produto_id: Annotated[int, Path(ge=1)],
    dados: ProdutoEstoque,
    user_atual: Usuario=Depends(require_funcionario),
    session: Session=Depends(get_db)
):
    return ProdutoService(session).atualizar_estoque(
        produto_id,
        dados.estoque
    )
