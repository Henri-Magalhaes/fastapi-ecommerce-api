import pytest
from http import HTTPStatus

from app.core.models_registry import Categoria, Produto

def test_listar_categorias_sem_token_retorna_200(client, products):
    response = client.get(
        url="/categories"
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert len(data) == 2

def test_listar_categorias_sem_nenhuma_retorna_lista_vazia(client):
    response = client.get(
        url="/categories"
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert not data

def test_listar_categorias_paginacao_respeita_limit_e_offset(client, products):
    response = client.get(
        url="/categories/?limit=1&offset=0"
    )

    assert response.status_code == HTTPStatus.OK
    
    data = response.json()["data"]

    assert len(data) == 1

    response2 = client.get(
        url="/categories/?limit=10&offset=1"
    )

    assert response2.status_code == HTTPStatus.OK

    data2 = response2.json()["data"]

    assert len(data2) == 1

@pytest.mark.parametrize("campo", [-23, "sçdç", 1000])
def test_listar_categorias_com_limit_invalido_retorna_422(client, products, campo):
    response = client.get(
        url=f"/categories/?limit={campo}&offset=0"
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


#GET /categorias/{id}
def test_buscar_categoria_existente_retorna_200(client, products):
    response = client.get(
        url="/categories/2"
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert data["nome"] == "ELETRONICO"

def test_buscar_categoria_sem_token_retorna_200(client, products):
    response = client.get(
        url="/categories/2"
    )

    assert response.status_code == HTTPStatus.OK

def test_buscar_categoria_inexistente_retorna_404(client):
    response = client.get(
        url="/categories/2"
    )

    assert response.status_code == HTTPStatus.NOT_FOUND

@pytest.mark.parametrize("campo", [-23, "ksfkld"])
def test_buscar_categoria_com_id_invalido_retorna_422(client, products, campo):
    response = client.get(
        url=f"/categories/{campo}"
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


#POST /categorias
def test_criar_categoria_como_funcionario_retorna_201(client, auth_header_funcionario):
    response = client.post(
        url="/categories",
        json={
            "nome": "ELETRONICOS"
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.CREATED

def test_criar_categoria_como_admin_retorna_201(client, auth_header_admin):
    response = client.post(
        url="/categories",
        json={
            "nome": "ELETRONICOS"
        },
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.CREATED

def test_criar_categoria_como_cliente_retorna_403(client, auth_header):
    response = client.post(
        url="/categories",
        json={
            "nome": "ELETRONICOS"
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.FORBIDDEN

def test_criar_categoria_sem_token_retorna_401(client):
    response = client.post(
        url="/categories",
        json={
            "nome": "ELETRONICOS"
        },
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

def test_criar_categoria_persiste_no_banco(client, auth_header_funcionario, db_session):
    response = client.post(
        url="/categories",
        json={
            "nome": "ELETRONICOS"
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.CREATED

    categoria = db_session.get(Categoria, 1)

    assert categoria.nome == "ELETRONICOS"

def test_criar_categoria_remove_espacos_nas_pontas_do_nome(client, auth_header_funcionario, db_session):
    response = client.post(
        url="/categories",
        json={
            "nome": "    eletronicos     "
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.CREATED

    categoria = db_session.get(Categoria, 1)

    assert categoria.nome == "ELETRONICOS"

def test_criar_categoria_com_nome_vazio_retorna_422(client, auth_header_funcionario):
    response = client.post(
        url="/categories",
        json={
            "nome": ""
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_criar_categoria_com_nome_so_espacos_retorna_422(client, auth_header_funcionario):
    response = client.post(
        url="/categories",
        json={
            "nome": "            "
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_criar_categoria_com_nome_maior_que_o_limite_retorna_422(client, auth_header_funcionario):
    response = client.post(
        url="/categories",
        json={
            "nome": "LLLLLLLLDÇSLÇDLÇSLDÇLSÇDLÇSLDÇLDÇLDSÇLDÇLSDÇLDSÇDLÇSDLÇDSLÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇÇSÇÇÇÇÇÇÇÇÇÇÇÇÇ"
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

@pytest.mark.parametrize("campo", [1212, -212, None, [], (), {}])
def test_criar_categoria_com_nome_de_tipo_errado_retorna_422(client, auth_header_funcionario, campo):
    response = client.post(
        url="/categories",
        json={
            "nome": campo
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_criar_categoria_com_body_vazio_retorna_422(client, auth_header_funcionario):
    response = client.post(
        url="/categories",
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_criar_categoria_com_nome_duplicado_retorna_409(client, auth_header_funcionario, products):
    response = client.post(
        url="/categories",
        json={
            "nome": "ELETRONICO"
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.CONFLICT

    message = response.json()["detail"]

    assert message == "Não é possivel criar essa categoria."

def test_criar_categoria_com_nome_duplicado_ignorando_minusculas_retorna_409(client, auth_header_funcionario, products):
    response = client.post(
        url="/categories",
        json={
            "nome": "eletronico"
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.CONFLICT

    message = response.json()["detail"]

    assert message == "Não é possivel criar essa categoria."

def test_criar_categoria_com_nome_duplicado_com_espacos_retorna_409(client, auth_header_funcionario, products):
    response = client.post(
        url="/categories",
        json={
            "nome": "    eletronico    "
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.CONFLICT

    message = response.json()["detail"]

    assert message == "Não é possivel criar essa categoria."

def test_criar_categoria_ignora_campos_protegidos_no_payload(client, auth_header_funcionario, db_session):
    response = client.post(
        url="/categories",
        json={
            "nome": "eletronico",
            "id": 12
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.CREATED

    categoria = db_session.get(Categoria, 1)

    assert categoria.id != 12
    assert categoria.id == 1


#PATCH /categorias/{id}
def test_editar_categoria_como_funcionario_retorna_200(client, auth_header_funcionario, products):
    response = client.patch(
        url="/categories/2",
        json={
            "nome": "LIVROS"
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

def test_editar_categoria_como_admin_retorna_200(client, auth_header_admin, products):
    response = client.patch(
        url="/categories/2",
        json={
            "nome": "LIVROS"
        },
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.OK

def test_editar_categoria_como_cliente_retorna_403(client, auth_header, products):
    response = client.patch(
        url="/categories/2",
        json={
            "nome": "LIVROS"
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.FORBIDDEN

def test_editar_categoria_sem_token_retorna_401(client, auth_header, products):
    response = client.patch(
        url="/categories/2",
        json={
            "nome": "LIVROS"
        }
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

def test_editar_categoria_inexistente_retorna_404(client, auth_header_admin):
    response = client.patch(
        url="/categories/2",
        json={
            "nome": "LIVROS"
        },
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.NOT_FOUND

    message = response.json()["detail"]

    assert message == "Categoria não encontrada."

def test_editar_nome_persiste_no_banco(client, auth_header_funcionario, products, db_session):
    response = client.patch(
        url="/categories/2",
        json={
            "nome": "LIVROS"
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

    categoria = db_session.get(Categoria, 2)

    assert categoria.nome == "LIVROS"

def test_editar_para_nome_ja_existente_retorna_409(client, auth_header_funcionario, products):
    response = client.patch(
        url="/categories/1",
        json={
            "nome": "ELETRONICO"
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.CONFLICT

    message = response.json()["detail"]

    assert message == "Não é possivel atualizar essa categoria."

def test_editar_para_o_proprio_nome_nao_retorna_409(client, auth_header_funcionario, products):
    response = client.patch(
        url="/categories/2",
        json={
            "nome": "ELETRONICO"
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

def test_editar_para_nome_vazio_ou_so_espacos_retorna_422(client, auth_header_funcionario, products):
    response = client.patch(
        url="/categories/2",
        json={
            "nome": "    "
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_editar_com_id_invalido_retorna_422(client, auth_header_funcionario, products):
    response = client.patch(
        url="/categories/-2",
        json={
            "nome": "LIVROS"
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_editar_ignora_campos_protegidos_no_payload(client, auth_header_funcionario, products, db_session):
    response = client.patch(
        url="/categories/2",
        json={
            "nome": "LIVROS",
            "id": 23
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

    categoria = db_session.get(Categoria, 2)

    assert categoria.nome == "LIVROS"
    assert categoria.id != 23
    assert categoria.id == 2

def test_editar_categoria_nao_altera_os_produtos_vinculados(client, auth_header_funcionario, products, db_session):
    response = client.patch(
        url="/categories/1",
        json={
            "nome": "LIVROS",
            "id": 23
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

    produto = db_session.get(Produto, 2)
    categoria = produto.categoria

    assert categoria.nome == "LIVROS"


#DELETE /categorias/{id}
def test_deletar_categoria_como_admin_retorna_200(client, auth_header_admin, products, db_session):
    categoria = Categoria(
        nome="LIVROS"
    )

    db_session.add(categoria)
    db_session.commit()

    response = client.delete(
        url="/categories/3",
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.OK

def test_deletar_categoria_como_cliente_retorna_403(client, auth_header, products):
    response = client.delete(
        url="/categories/2",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.FORBIDDEN

def test_deletar_categoria_sem_token_retorna_401(client, products):
    response = client.delete(
        url="/categories/2"
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

def test_deletar_categoria_como_funcionario_retorna_200(client, auth_header_funcionario, products, db_session):
    categoria = Categoria(
            nome="LIVROS"
        )
    
    db_session.add(categoria)
    db_session.commit()

    response = client.delete(
        url="/categories/3",
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

def test_deletar_categoria_sem_produtos_retorna_200_com_data_none(client, auth_header_admin, products, db_session):
    categoria = Categoria(
            nome="LIVROS"
        )
    
    db_session.add(categoria)
    db_session.commit()

    response = client.delete(
        url="/categories/3",
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()['data']

    assert data is None

def test_deletar_categoria_remove_do_banco(client, auth_header_admin, products, db_session):
    categoria = Categoria(
                nome="LIVROS"
            )
        
    db_session.add(categoria)
    db_session.commit()

    response = client.delete(
        url="/categories/3",
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.OK

    categoria_deletada = db_session.get(Categoria, 3)

    assert categoria_deletada is None

def test_deletar_categoria_inexistente_retorna_404(client, auth_header_admin, products, db_session):
    response = client.delete(
        url="/categories/3",
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.NOT_FOUND

    message = response.json()["detail"]

    assert message == "Categoria não encontrada."

def test_deletar_categoria_com_produtos_retorna_409(client, auth_header_admin, products):
    response = client.delete(
        url="/categories/2",
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.CONFLICT

    message = response.json()["detail"]
    
    assert message == "Não foi possivel deletar essa categoria."

def test_deletar_categoria_com_produtos_nao_remove_nada(client, auth_header_admin, products, db_session):
    response = client.delete(
        url="/categories/2",
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.CONFLICT

    categoria = db_session.get(Categoria, 2)
    produtos = categoria.produtos

    assert categoria is not None

    for produto in produtos:
        assert produto.id_categoria == categoria.id

def test_deletar_categoria_com_id_invalido_retorna_422(client, auth_header_admin, products):
    response = client.delete(
        url="/categories/-2",
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_deletar_categoria_ja_removida_retorna_404(client, auth_header_admin, products, db_session):
    categoria = Categoria(
        nome="LIVROS"
    )

    db_session.add(categoria)
    db_session.commit()
    
    response = client.delete(
        url="/categories/3",
        headers=auth_header_admin
    )

    print(response.json())

    assert response.status_code == HTTPStatus.OK

    response2 = client.delete(
        url="/categories/3",
        headers=auth_header_admin
    )

    assert response2.status_code == HTTPStatus.NOT_FOUND

