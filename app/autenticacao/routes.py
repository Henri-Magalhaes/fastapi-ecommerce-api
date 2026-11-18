from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from http import HTTPStatus
from sqlalchemy.orm import Session

from app.autenticacao.schemas import RegisterInput
from app.core.schemas import ApiResponse
from app.users.schemas import UserResponse
from app.autenticacao.services import AuthService
from app.core.dependencies import get_user
from app.users.models import Usuario
from app.core.database import get_db

auth_router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)

@auth_router.post("/register", status_code=HTTPStatus.CREATED, response_model=ApiResponse[UserResponse])
async def registrar_usuario(dados: RegisterInput, sessao: Session=Depends(get_db)):
    return AuthService(sessao).registrar_usuario(dados.nome, dados.email, dados.senha)

@auth_router.post("/login")
async def login_usuario(dados: OAuth2PasswordRequestForm=Depends(), sessao: Session=Depends(get_db)):
    return AuthService(sessao).login_usuario(dados.username, dados.password)

@auth_router.get("/me", response_model=ApiResponse[UserResponse])
async def me(user: Usuario=Depends(get_user)):
    return {
        "success": True,
        "message": f"Acessado pelo usuário {user.id}.",
        "data": user
    }
