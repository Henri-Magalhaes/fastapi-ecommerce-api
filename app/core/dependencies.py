import jwt

from sqlalchemy.orm import Session
from http import HTTPStatus
from fastapi import HTTPException, Depends

from app.core.security import oauth2_scheme
from app.core.config import settings
from app.users.repository import UserRepository
from app.core.database import get_db
from app.users.models import Usuario, RoleEnum

def get_user(token: str=Depends(oauth2_scheme), sessao: Session=Depends(get_db)) -> Usuario:
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail="token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={
                "require": ["sub", "exp"]
            }
        )

        type_token = payload.get("type")
        user_id = int(payload.get("sub"))

        if type_token != "access":
            raise credentials_exception

        if user_id is None:
            raise credentials_exception

        user = UserRepository(sessao).buscar_por_id(user_id)

        if user is None:
            raise credentials_exception

        return user
        
    except jwt.ImmatureSignatureError:
        raise credentials_exception
    
    except jwt.DecodeError:
        raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise credentials_exception

    except jwt.InvalidTokenError:
        raise credentials_exception

    except ValueError:
        raise credentials_exception

    except TypeError:
        raise credentials_exception

def require_admin(user_atual: Usuario=Depends(get_user)) -> Usuario:
    if user_atual.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Acesso permitido somente para administradores."
        )

    return user_atual

def require_cliente(user_atual: Usuario=Depends(get_user)) -> Usuario:
    if not user_atual.role in (RoleEnum.CLIENTE, RoleEnum.ADMIN):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Acesso permitido somente para clientes."
        )

    return user_atual

def require_funcionario(user_atual: Usuario=Depends(get_user)) -> Usuario:
    if not user_atual.role in (RoleEnum.FUNCIONARIO, RoleEnum.ADMIN):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Acesso permitido somente para funcionarios."
        )

    return user_atual