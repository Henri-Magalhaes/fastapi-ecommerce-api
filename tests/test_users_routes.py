import pytest
from http import HTTPStatus

from app.users.models import Usuario, RoleEnum

#GET /usuarios
def test_listar_usuarios_como_admin_retorna_200(client, auth_header_admin, users_clientes):
    response = client.get(
        url="/users/?limit=10&offset=0&role=CLIENTE",
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.OK

    dados = response.json()["data"]

    assert isinstance(dados, list)

    tamanho_lista = len(dados)

    assert tamanho_lista == 10

def test_listar_usuarios_como_cliente_retorna_403(client, auth_header):
    response = client.get(
        url="/users/?limit=10&offset=0&role=CLIENTE",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.FORBIDDEN

    dados = response.json()

    assert dados["detail"] == "Acesso permitido somente para funcionarios."

def test_listar_usuarios_sem_token_retorna_401(client):
    response = client.get(
        url="/users/?limit=10&offset=0&role=CLIENTE",
    )
    
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    dados = response.json()

    assert dados["detail"] == "Not authenticated"

def test_listar_usuarios_nao_retorna_senha_hash(client, auth_header_admin, users_clientes):
    response = client.get(
        url="/users/?limit=10&offset=0&role=CLIENTE",
        headers=auth_header_admin
    )
    
    assert response.status_code == HTTPStatus.OK
    
    dados = response.json()["data"]
    user = dados[1]

    assert not "hash_senha" in user

def test_listar_usuarios_como_funcionario_retorna_200(client, auth_header_funcionario):
    response = client.get(
        url="/users/?limit=10&offset=0&role=CLIENTE",
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

def test_listar_usuarios_paginacao_respeita_limit_e_offset(client, auth_header_admin, users_clientes):
    response = client.get(
        url="/users/?limit=2&offset=0&role=CLIENTE",
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert len(data) == 2

def test_listar_usuarios_pagina_alem_do_total_retorna_lista_vazia(client, auth_header_admin, users_clientes):
    response = client.get(
        url="/users/?limit=2&offset=15&role=CLIENTE",
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.OK
    
    data = response.json()["data"]

    assert not data

@pytest.mark.parametrize("campo", [-1, 0, 101])
def test_listar_usuarios_com_limit_invalido_retorna_422(client, auth_header_admin, users_clientes, campo):
    response = client.get(
        url=f"/users/?limit={campo}&offset=15&role=CLIENTE",
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_listar_usuarios_como_funcionario_lista_apenas_clientes(client, auth_header_funcionario, users_clientes):
    response = client.get(
        url="/users/?limit=10&offset=0&role=ADMIN",
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert len(data) == 10


#GET /usuarios/{id}
def test_buscar_usuario_proprio_retorna_200(client, auth_header):
    response = client.get(
        url="/users/1",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()['data']

    assert data["id"] == 1
    assert data["nome"] == "Novo Usuario"
    assert data["email"] == "novousuario@gmail.com"
    assert "dt_criacao" in data

def test_buscar_usuario_de_outro_como_cliente_retorna_403(client, auth_header, users_clientes):
    response = client.get(
        url="/users/2",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.FORBIDDEN

    data = response.json()

    assert data["detail"] == "Ação não permitida."

def test_buscar_usuario_qualquer_como_admin_retorna_200(client, auth_header_admin, users_clientes):
    response = client.get(
        url="/users/5",
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert data["id"] == 5
    assert data["nome"] == "User Teste 4"
    assert data["email"] == "userteste4@gmail.com"
    assert "dt_criacao" in data

def test_buscar_usuario_inexistente_retorna_404(client, auth_header_admin):
    response = client.get(
        url="/users/5",
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.NOT_FOUND

    data = response.json()

    assert data["detail"] == "Usuário não encontrado."

def test_buscar_usuario_sem_token_retorna_401(client, user_cliente):
    response = client.get(
        url="/users/5",
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

    data = response.json()

    assert data["detail"] == "Not authenticated"

def test_buscar_usuario_nao_retorna_senha_hash(client, auth_header):
    response = client.get(
        url="/users/1",
        headers=auth_header
    )
    
    assert response.status_code == HTTPStatus.OK
    
    data = response.json()['data']

    assert not "hash_senha" in data

@pytest.mark.parametrize("campo", [-1, "hsosi"])
def test_buscar_usuario_com_id_invalido_retorna_422(client, auth_header, campo):
    response = client.get(
        url=f"/users/{campo}",
        headers=auth_header
    )
        
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_buscar_usuario_inexistente_como_cliente_nao_revela_existencia(client, auth_header):
    response = client.get(
        url="/users/5",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.FORBIDDEN

    data = response.json()

    assert data["detail"] == "Ação não permitida."

def test_buscar_usuario_cliente_como_funcionario_retorna_200(client, auth_header_funcionario, users_clientes):
    response = client.get(
        url="/users/5",
        headers=auth_header_funcionario
    )
    
    assert response.status_code == HTTPStatus.OK

    data = response.json()['data']
    
    assert data["id"] == 5
    assert data["nome"] == "User Teste 4"
    assert data["email"] == "userteste4@gmail.com"
    assert "dt_criacao" in data

def test_buscar_usuario_admin_como_funcionario_retorna_404(client, auth_header_funcionario, user_admin):
    response = client.get(
        url="/users/2",
        headers=auth_header_funcionario
    )
        
    assert response.status_code == HTTPStatus.NOT_FOUND

    data = response.json()

    assert data["detail"] == "Usuário não encontrado."


#PATCH /usuarios/{id}
def test_atualizar_proprio_usuario_retorna_200(client, auth_header, db_session):
    user_antes = db_session.get(Usuario, 1)

    assert user_antes.nome == "Novo Usuario"
    assert user_antes.email == "novousuario@gmail.com"
    
    response = client.patch(
        url="/users/me",
        json={
            "nome": "User Atualizado",
            "email": "emailnovo@gmail.com"
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.OK

    user_depois = db_session.get(Usuario, 1)

    assert user_depois.nome == "User Atualizado"
    assert user_depois.email == "emailnovo@gmail.com"

def test_atualizar_usuario_sem_token_retorna_401(client, user_cliente):
    response = client.patch(
        url="/users/me",
        json={
            "nome": "User Atualizado",
            "email": "emailnovo@gmail.com"
        }
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

def test_atualizar_ignora_campo_role_no_payload(client, auth_header, db_session):
    response = client.patch(
        url="/users/me",
        json={
            "nome": "User Atualizado",
            "email": "emailnovo@gmail.com",
            "role": "ADMIN"
        },
        headers=auth_header
    )
    
    assert response.status_code == HTTPStatus.OK
    
    user_depois = db_session.get(Usuario, 1)

    assert user_depois.role == RoleEnum.CLIENTE

def test_atualizar_ignora_campos_protegidos(client, auth_header, db_session):
    user_antes = db_session.get(Usuario, 1)
    
    nome_antes = user_antes.nome
    email_antes = user_antes.email
    id_antes = user_antes.id
    hash_senha_antes = user_antes.hash_senha
    dt_criacao_antes = user_antes.dt_criacao
        
    response = client.patch(
        url="/users/me",
        json={
            "nome": "User Atualizado",
            "email": "emailnovo@gmail.com",
            "id": 100,
            "hash_senha": "sem-hash",
            "dt_criacao": "agora"
        },
        headers=auth_header
    )
    
    assert response.status_code == HTTPStatus.OK

    db_session.expire_all()

    user_depois = db_session.get(Usuario, 1)

    assert user_depois.nome != nome_antes
    assert user_depois.email != email_antes

    assert user_depois.id == id_antes
    assert user_depois.hash_senha == hash_senha_antes
    assert user_depois.dt_criacao == dt_criacao_antes

def test_atualizar_email_para_um_ja_existente_retorna_409(client, auth_header, users_clientes):
    response = client.patch(
        url="/users/me",
        json={
            "nome": "User Atualizado",
            "email": "userteste4@gmail.com"
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.CONFLICT

    data = response.json()

    assert data["detail"] == "Não foi possível atualizar os dados devido a um conflito de integridade."

def test_atualizar_email_invalido_retorna_422(client, auth_header):
    response = client.patch(
        url="/users/me",
        json={
            "nome": "User Atualizado",
            "email": "emailinvalido"
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_atualizar_email_normaliza_para_minusculo(client, auth_header, db_session):
    response = client.patch(
        url="/users/me",
        json={
            "nome": "User Atualizado",
            "email": "NOVOEMAIL@GMAIL.COM"
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.OK

    user_atualizado = db_session.get(Usuario, 1)

    assert user_atualizado.email == "novoemail@gmail.com"

def test_atualizar_com_payload_vazio_retorna_422(client, auth_header):
    response = client.patch(
        url="/users/me",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_atualizar_parcialmente_nao_altera_campos_omitidos(client, auth_header, db_session):
    user_antes = db_session.get(Usuario, 1)
        
    nome_antes = user_antes.nome
    email_antes = user_antes.email
    
    response = client.patch(
        url="/users/me",
        json={
            "nome": "User Atualizado"
        },
        headers=auth_header
    )
        
    assert response.status_code == HTTPStatus.OK

    db_session.expire_all()

    user_depois = db_session.get(Usuario, 1)

    assert user_depois.nome != nome_antes
    assert user_depois.email == email_antes

def test_atualizar_nome_vazio_ou_so_espacos_retorna_422(client, auth_header):
    response = client.patch(
        url="/users/me",
        json={
            "nome": "     ",
            "email": "emailnovo@gmail.com"
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


#PATCH /usuarios/{id}/role
def test_alterar_role_como_admin_retorna_200(client, auth_header_admin, users_clientes, db_session):
    response = client.patch(
        url="/users/2/role",
        json={
            "role": RoleEnum.ADMIN
        },
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.OK

    user_atualizado = db_session.get(Usuario, 2)

    assert user_atualizado.role == RoleEnum.ADMIN

def test_alterar_role_como_cliente_retorna_403(client, auth_header, users_clientes):
    response = client.patch(
        url="/users/2/role",
        json={
            "role": RoleEnum.ADMIN
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.FORBIDDEN

def test_alterar_role_como_funcionario_retorna_403(client, auth_header_funcionario, users_clientes):
    response = client.patch(
        url="/users/2/role",
        json={
            "role": RoleEnum.ADMIN
        },
        headers=auth_header_funcionario
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN

def test_cliente_nao_consegue_promover_a_si_mesmo(client, auth_header):
    response = client.patch(
        url="/users/1/role",
        json={
            "role": RoleEnum.ADMIN
        },
        headers=auth_header
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN

def test_alterar_role_sem_token_retorna_401(client, users_clientes):
    response = client.patch(
        url="/users/1/role",
        json={
            "role": RoleEnum.ADMIN
        }
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

def test_alterar_role_para_valor_invalido_retorna_422(client, auth_header_admin, users_clientes):
    response = client.patch(
        url="/users/2/role",
        json={
            "role": "superusuario"
        },
        headers=auth_header_admin
    )
    
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_alterar_role_de_usuario_inexistente_retorna_404(client, auth_header_admin):
    response = client.patch(
        url="/users/2/role",
        json={
            "role": RoleEnum.ADMIN
        },
        headers=auth_header_admin
    )
        
    assert response.status_code == HTTPStatus.NOT_FOUND
