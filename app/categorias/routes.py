from fastapi import APIRouter, Depends, Path, Body, Query
from typing import Annotated
from sqlalchemy.orm import Session
from http import HTTPStatus

from app.core.models_registry import Usuario
from app.core.schemas import ApiResponse
from app.categorias.services import CategoriaService
from app.categorias.schemas import CategoriaResponse, CategoriaFilter, CategoriaCreate
from app.core.database import get_db
from app.core.dependencies import require_funcionario

category_router = APIRouter(
    prefix="/categories",
    tags=["Categorias"]
)

@category_router.get("/", response_model=ApiResponse[list[CategoriaResponse]])
async def listar_categorias(
    dados: Annotated[CategoriaFilter, Query()],
    session: Session=Depends(get_db)
):
    return CategoriaService(session).listar_categorias(
        dados
    )

@category_router.get("/{id_categoria}", response_model=ApiResponse[CategoriaResponse])
async def mostrar_detalhes_categoria(
    id_categoria: Annotated[int, Path(ge=1)],
    session: Session=Depends(get_db)
):
    return CategoriaService(session).buscar_categoria_por_id(
        id_categoria
    )

@category_router.post("/", status_code=HTTPStatus.CREATED, response_model=ApiResponse[CategoriaResponse])
async def criar_nova_categoria(
    dados: CategoriaCreate,
    func_atual: Usuario=Depends(require_funcionario),
    session: Session=Depends(get_db)
):
    return CategoriaService(session).criar_nova_categoria(
        dados.nome
    )

@category_router.patch("/{id_categoria}", response_model=ApiResponse[CategoriaResponse])
async def atualizar_categoria(
    id_categoria: Annotated[int, Path(ge=1)],
    dados: Annotated[CategoriaCreate, Body()],
    func_atual: Usuario=Depends(require_funcionario),
    session: Session=Depends(get_db)
):
    return CategoriaService(session).atualizar_categoria(
        dados.nome,
        id_categoria
    )

@category_router.delete("/{id_categoria}", response_model=ApiResponse[None])
async def deletar_categoria(
    id_categoria: Annotated[int, Path(ge=1)],
    func_atual: Usuario=Depends(require_funcionario),
    session: Session=Depends(get_db)
):
    return CategoriaService(session).remover_categoria(
        id_categoria
    )
