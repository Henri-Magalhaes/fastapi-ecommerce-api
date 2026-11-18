from typing import Annotated
from fastapi import APIRouter, Depends, Query, Path

from sqlalchemy.orm import Session

from app.core.schemas import ApiResponse
from app.users.schemas import UserResponse, UsuarioPaginatedResponse, UserUpdate, UserRoleUpdate, UserPedidosResponse
from app.core.dependencies import require_admin, get_user, require_funcionario
from app.core.database import get_db
from app.users.models import Usuario
from app.users.services import UserService

users_router = APIRouter(
    prefix="/users",
    tags=["Usuários"]
)

@users_router.get("/", response_model=ApiResponse[list[UserResponse]])
async def listar_usuarios(dados: Annotated[UsuarioPaginatedResponse, Query()],
                          user_atual: Usuario=Depends(require_funcionario),
                          session: Session=Depends(get_db)
                        ):
    return UserService(session).listar_usuarios(
        user_atual,
        dados.limit,
        dados.offset,
        dados.role
    )

@users_router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def mostrar_dados(user_id: Annotated[int, Path(ge=1)], 
                        user_atual: Usuario=Depends(get_user),
                        session: Session=Depends(get_db)
                        ):
    return UserService(session).mostrar_dados(
        user_atual,
        user_id,
    )

@users_router.patch("/me", response_model=ApiResponse[UserResponse])
async def atualizar_dados(dados: UserUpdate,
                        user_atual: Usuario=Depends(get_user),
                        session: Session=Depends(get_db)
                        ):
    return UserService(session).atualizar_dados_usuario(
        user_atual,
        dados
    )

@users_router.patch("/{user_id}/role", response_model=ApiResponse[UserResponse])
async def alterar_role(user_id: Annotated[int, Path(ge=1)],
                       role: UserRoleUpdate,
                       admin: Usuario=Depends(require_admin),
                       session: Session=Depends(get_db)
                    ):
    return UserService(session).alterar_role_usuario(
        user_id,
        role.role
    )
