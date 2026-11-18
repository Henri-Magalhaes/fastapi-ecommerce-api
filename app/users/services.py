from dataclasses import dataclass, field
from fastapi import HTTPException
from http import HTTPStatus

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.users.repository import UserRepository
from app.users.models import Usuario
from app.users.models import RoleEnum
from app.users.schemas import UserUpdate

@dataclass
class UserService:
    _db: Session
    _user_repo: UserRepository = field(init=False)

    def __post_init__(self):
        self._user_repo = UserRepository(self._db)

    def listar_usuarios(self, user_atual: Usuario, limit: int, offset: int, role: RoleEnum) -> dict[str, bool | str | list[Usuario]]:
        if user_atual.role == RoleEnum.FUNCIONARIO:
            role = RoleEnum.CLIENTE

        users = self._user_repo.listar_usuarios(
            limit,
            offset,
            role
        )

        if not users:
            return {
                "success": True,
                "message": "Usuários não encontrados.",
                "data": []
            }

        return {
            "success": True,
            "message": "Usuários encontrados.",
            "data": users
        }

    def mostrar_dados(self, user_atual: Usuario, user_id: int) -> dict[str, bool | str | Usuario]:
        if user_atual.role in (RoleEnum.ADMIN, RoleEnum.FUNCIONARIO):
            user = self._user_repo.buscar_por_id(user_id)

            if user is None:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail="Usuário não encontrado."
                )

            if user_atual.role == RoleEnum.FUNCIONARIO:
                if user.role != RoleEnum.CLIENTE:
                    raise HTTPException(
                        status_code=HTTPStatus.NOT_FOUND,
                        detail="Usuário não encontrado."
                )

            return {
                "success": True,
                "message": f"Usuário {user.id} encontrado.",
                "data": user
            }

        if user_atual.id != user_id:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="Ação não permitida."
            )

        return {
            "success": True,
            "message": f"Usuário {user_atual.id} encontrado.",
            "data": user_atual
        }

    def atualizar_dados_usuario(self, user_atual: Usuario, dados: UserUpdate) -> dict[str, bool | str | Usuario]:
        dados_atualizados = dados.model_dump(exclude_unset=True)

        try:
            self._user_repo.atualizar_dados_user(
                user_atual,
                dados_atualizados
            )

            self._db.commit()
            self._db.refresh(user_atual)

            return {
                "success": True,
                "message": f"Usuário {user_atual.id} atualizado.",
                "data": user_atual
            }

        except IntegrityError:
            self._db.rollback()
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="Não foi possível atualizar os dados devido a um conflito de integridade."
            )

    def alterar_role_usuario(self, user_id: int, nova_role: RoleEnum) -> dict[str, bool | str | Usuario]:
        user = self._user_repo.buscar_por_id(user_id)

        if user is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Usuário não encontrado."
            )

        user_alterado = self._user_repo.alterar_role(
            user,
            nova_role
        )

        self._db.commit()
        self._db.refresh(user_alterado)

        return {
            "success": True,
            "message": f"Role do usuário {user_alterado.id} alterada.",
            "data": user_alterado
        }
