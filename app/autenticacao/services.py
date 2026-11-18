import pydantic
from dataclasses import dataclass, field
from fastapi import HTTPException
from http import HTTPStatus

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.users.repository import UserRepository
from app.users.models import Usuario
from app.core.security import hash_password, verify_hash_password, create_access_token
from app.autenticacao.schemas import LoginInput

@dataclass
class AuthService:
    _session: Session
    _user_repo: UserRepository = field(init=False)

    def __post_init__(self):
        self._user_repo = UserRepository(self._session)

    def registrar_usuario(self, nome: str, email: str, senha: str) -> dict[str, bool | str | Usuario]:
        if self._user_repo.buscar_por_email(email):
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="Usuario já cadastrado"
            )

        hash_senha = hash_password(senha)

        try:
            user = self._user_repo.adicionar_usuario(
                nome,
                email,
                hash_senha
            )

            self._session.commit()
            
            return {
                "success": True,
                "message": f"Usuário {user.id} cadastrado.",
                "data": user
            }
        
        except IntegrityError:
            self._session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="Não foi possivel cadastrar o usuario"
            )

    def login_usuario(self, email: str, senha: str) -> dict[str, bool | str ]:
        try:
            dados_validados = LoginInput(
                email=email,
                senha=senha
            )

        except pydantic.ValidationError:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Email ou senha inválidos"
            )
        

        user = self._user_repo.buscar_por_email(dados_validados.email)

        if user is None:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Email ou senha inválidos"
            )

        if not verify_hash_password(dados_validados.senha, user.hash_senha):
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Email ou senha inválidos"
            )

        access_token = create_access_token(user.id, user.role)

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
