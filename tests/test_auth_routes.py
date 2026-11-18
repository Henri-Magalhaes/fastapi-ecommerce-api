import pytest
import jwt

from http import HTTPStatus

from app.users.models import Usuario
from app.core.config import settings

#/auth/register
def test_registrar_sucesso_novo_usuario(client, db_session):
    response = client.post(
        url="/auth/register",
        json={
            "nome": "Novo Usuario",
            "email": "usuarionovo@gmail.com",
            "senha": "Teste123"
        }
    )

    assert response.status_code == HTTPStatus.CREATED

    dados = response.json()["data"]

    assert dados["id"] == 1
    assert dados["nome"] == "Novo Usuario"
    assert dados["email"] == "usuarionovo@gmail.com"

    user = db_session.get(Usuario, dados["id"])

    assert not user is None

def test_registro_salva_senha_com_hash(client, db_session):
    response = client.post(
            url="/auth/register",
            json={
                "nome": "Novo Usuario",
                "email": "usuarionovo@gmail.com",
                "senha": "Teste123"
            }
        )

    dados = response.json()['data']
    user = db_session.get(Usuario, dados["id"])

    assert user.hash_senha != "Teste123"

def test_registro_com_email_duplicado_retorna_409(client):
    response01 = client.post(
            url="/auth/register",
            json={
                "nome": "Novo Usuario",
                "email": "usuarionovo@gmail.com",
                "senha": "Teste123"
            }
        )

    assert response01.status_code == HTTPStatus.CREATED

    response02 = client.post(
            url="/auth/register",
            json={
                "nome": "Novo Usuario2",
                "email": "usuarionovo@gmail.com",
                "senha": "NovaSenha123"
            }
        )

    assert response02.status_code == HTTPStatus.CONFLICT

    dados = response02.json()

    assert dados["detail"] == "Usuario já cadastrado"

def test_registro_com_email_invalido_retorna_422(client):
    response = client.post(
            url="/auth/register",
            json={
                "nome": "Novo Usuario",
                "email": "email_invalido",
                "senha": "Teste123"
            }
        )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

@pytest.mark.parametrize("campo", ["nome", "email", "senha"])
def test_registro_sem_campos_obrigatorios_retorna_422(client, campo):
    dados = {
        "nome": "Novo Usuario",
        "email": "novousuario@gmail.com",
        "senha": "Teste12345"
    }

    dados.pop(campo)

    response = client.post(
        url="/auth/register",
        json=dados
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_registro_com_senha_fraca_retorna_422(client):
    response = client.post(
                url="/auth/register",
                json={
                    "nome": "Novo Usuario",
                    "email": "email_invalido",
                    "senha": "teste"
                }
            )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_registro_cria_usuario_com_role_cliente_por_padrao(client, db_session):
    response = client.post(
            url="/auth/register",
            json={
                "nome": "Novo Usuario",
                "email": "usuarionovo@gmail.com",
                "senha": "Teste123"
            }
        )
    
    user = db_session.get(Usuario, 1)

    assert user.role == "CLIENTE"

def test_registro_ignora_role_enviada_no_payload(client, db_session):
    response = client.post(
                url="/auth/register",
                json={
                    "nome": "Novo Usuario",
                    "email": "usuarionovo@gmail.com",
                    "senha": "Teste123",
                    "role": "ADMIN"
                }
            )

    assert response.status_code == HTTPStatus.CREATED

    user = db_session.get(Usuario, 1)

    assert user.role == "CLIENTE"

def test_registro_normaliza_email_para_minusculo(client):
    response01 = client.post(
                url="/auth/register",
                json={
                    "nome": "Novo Usuario",
                    "email": "usuarionovo@gmail.com",
                    "senha": "Teste123"
                }
            )
    
    assert response01.status_code == HTTPStatus.CREATED
    
    response02 = client.post(
                url="/auth/register",
                json={
                    "nome": "Novo Usuario2",
                    "email": "Usuarionovo@gmail.com",
                    "senha": "NovaSenha123"
                }
            )
    
    assert response02.status_code == HTTPStatus.CONFLICT


#/auth/login
def test_login_com_credenciais_validas_retorna_token(client, user_cliente):
    response = client.post(
        url="/auth/login",
        data={
            "username": "novousuario@gmail.com",
            "password": "Teste123"
        }
    )

    assert response.status_code == HTTPStatus.OK

    dados = response.json()

    assert "access_token" in dados
    assert dados["token_type"] == "bearer"

def test_login_com_senha_errada_retorna_401(client, user_cliente):
    response = client.post(
            url="/auth/login",
            data={
                "username": "novousuario@gmail.com",
                "password": "teste123"
            }
        )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

    dados = response.json()

    assert dados["detail"] == "Email ou senha inválidos"

def test_login_com_email_inexistente_retorna_401(client, user_cliente):
    response = client.post(
                url="/auth/login",
                data={
                    "username": "outroemail@gmail.com",
                    "password": "teste123"
                }
            )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

    dados = response.json()

    assert dados["detail"] == "Email ou senha inválidos"

@pytest.mark.parametrize("campo", ["username", "password"])
def test_login_sem_campos_retorna_422(client, user_cliente, campo):
    dados = {
        "username": "novousuario@gmail.com",
        "password": "Teste123"
    }

    dados.pop(campo)

    response = client.post(
            url="/auth/login",
            data=dados
        )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_login_token_contem_claims_esperadas(client, user_cliente):
    response = client.post(
            url="/auth/login",
            data={
                "username": "novousuario@gmail.com",
                "password": "Teste123"
            }
        )

    assert response.status_code == HTTPStatus.OK

    dados = response.json()
    token = dados["access_token"]

    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm]
    )

    assert payload["sub"] == '1'
    assert payload["role"] == "CLIENTE"
    assert payload["type"] == "access"
    assert "exp" in payload


#/auth/me
def test_me_com_token_valido_retorna_usuario_logado(client, auth_header):
    response = client.get(
        url="/auth/me",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.OK

    dados = response.json()["data"]

    assert dados["id"] == 1
    assert dados["nome"] == "Novo Usuario"
    assert dados["email"] == "novousuario@gmail.com"
    assert "dt_criacao" in dados

def test_me_sem_token_retorna_401(client):
    response = client.get(
            url="/auth/me",
        )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

def test_me_com_token_invalido_retorna_401(client):
    response = client.get(
            url="/auth/me",
            headers={
                "Authorization": f"Bearer token_invalido",
            }
        )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["detail"] == "token inválido ou expirado"

def test_me_com_token_expirado_retorna_401(client, invalid_auth_header):
    response = client.get(
            url="/auth/me",
            headers=invalid_auth_header
        )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["detail"] == "token inválido ou expirado"
