import pytest
from http import HTTPStatus

#GET /produtos
def test_listar_produtos_sem_token_retorna_200(client):
    response = client.get(
        url="/products/?limit=15&offset=0"
    )

    assert response.status_code == HTTPStatus.OK

urls = [
    ("/products/?limit=10&offset=0", 10),
    ("/products/?limit=10&offset=5", 5),
    ("/products/?limit=10&offset=0&categoria=ALIMENTO", 5)
]
@pytest.mark.parametrize("url, resultado", urls)
def test_listar_produtos_paginacao_respeita_limit_offset_e_categoria(client, products, url, resultado):
    response = client.get(
        url=url,
    )

    data = response.json()["data"]

    assert len(data) == resultado

def test_listar_produtos_limit_acima_do_maximo_retorna_422(client):
    response = client.get(
        url="/products/?limit=101&offset=0"
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_listar_produtos_sem_resultados_retorna_lista_vazia(client):
    response = client.get(
        url="/products/?limit=15&offset=0"
    )

    data = response.json()["data"]

    assert not data


#GET /produtos/{id}
def test_buscar_produto_existente_retorna_200(client, products):
    response = client.get(
        url="/products/6"
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert data["nome"] == "Produto 6"
    assert data["categoria"]["nome"] == "ELETRONICO"

def test_buscar_produto_inexistente_retorna_404(client):
    response = client.get(
        url="/products/6"
    )

    assert response.status_code == HTTPStatus.NOT_FOUND

@pytest.mark.parametrize("campo", [-1, "kfsokfo"])
def test_buscar_produto_id_invalido_retorna_422(client, campo):
    response = client.get(
        url=f"/products/{campo}"
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


#POST /produtos
def test_criar_produto_como_funcionario_retorna_201(client, products, auth_header_funcionario):
    response = client.post(
        url="/products/",
        json={
            "nome": "Produto Teste",
            "id_categoria": 2,
            "valor_unitario": "2.99",
            "estoque": 53
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.CREATED

    data = response.json()["data"]

    assert data["nome"] == "Produto Teste"
    assert data["categoria"]["nome"] == "ELETRONICO"

def test_criar_produto_como_admin_retorna_201(client, products, auth_header_admin):
    response = client.post(
        url="/products/",
        json={
            "nome": "Produto Teste",
            "id_categoria": 2,
            "valor_unitario": "2.99",
            "estoque": 53
        },
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.CREATED

    data = response.json()["data"]

    assert data["nome"] == "Produto Teste"
    assert data["categoria"]["nome"] == "ELETRONICO"

def test_criar_produto_como_cliente_retorna_403(client, products, auth_header):
    response = client.post(
        url="/products/",
        json={
            "nome": "Produto Teste",
            "id_categoria": 2,
            "valor_unitario": "2.99",
            "estoque": 53
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.FORBIDDEN

def test_criar_produto_sem_token_retorna_401(client, products):
    response = client.post(
        url="/products/",
        json={
            "nome": "Produto Teste",
            "id_categoria": 2,
            "valor_unitario": "2.99",
            "estoque": 53
        }
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

@pytest.mark.parametrize("campo", ["-1.0"])
def test_criar_produto_negativo_retorna_422(client, products, auth_header_funcionario, campo):
    response = client.post(
        url="/products/",
        json={
            "nome": "Produto Teste",
            "id_categoria": 2,
            "valor_unitario": campo,
            "estoque": 53
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_criar_produto_estoque_negativo_retorna_422(client, products, auth_header_funcionario):
    response = client.post(
        url="/products/",
        json={
            "nome": "Produto Teste",
            "id_categoria": 2,
            "valor_unitario": "2.99",
            "estoque": -12
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

@pytest.mark.parametrize("campo", ["", "       "])
def test_criar_produto_sem_nome_retorna_422(client, products, auth_header_funcionario, campo):
    response = client.post(
        url="/products/",
        json={
            "nome": campo,
            "id_categoria": 2,
            "valor_unitario": "2.99",
            "estoque": 53
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_criar_produto_nome_duplicado_retorna_409(client, products, auth_header_funcionario):
    response = client.post(
        url="/products/",
        json={
            "nome": "Produto 4",
            "id_categoria": 2,
            "valor_unitario": "2.99",
            "estoque": 53
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.CONFLICT


#PATCH /produtos/{id}
def test_atualizar_produto_como_funcionario_retorna_200(client, products, auth_header_funcionario):
    response = client.patch(
        url="/products/5",
        json={
            "nome": "Novo Produto",
            "id_categoria": 2,
            "valor_unitario": "55.0"
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert data["nome"] == "Novo Produto"
    assert data["categoria"]["nome"] == "ELETRONICO"

def test_atualizar_produto_atualiza_apenas_campos_enviados(client, products, auth_header_funcionario):
    response = client.patch(
        url="/products/5",
        json={
            "id_categoria": 2,
            "valor_unitario": "55.0"
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert data["nome"] == "Produto 5"
    assert data["categoria"]["nome"] == "ELETRONICO"

def test_atualizar_produto_como_cliente_retorna_403(client, products, auth_header):
    response = client.patch(
        url="/products/5",
        json={
            "nome": "Novo Produto",
            "id_categoria": 2,
            "valor_unitario": "55.0"
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.FORBIDDEN

def test_atualizar_produto_sem_token_retorna_401(client, products):
    response = client.patch(
        url="/products/5",
        json={
            "nome": "Novo Produto",
            "id_categoria": 2,
            "valor_unitario": "55.0"
        }
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

def test_atualizar_produto_inexistente_retorna_404(client, auth_header_funcionario):
    response = client.patch(
        url="/products/5",
        json={
            "nome": "Novo Produto",
            "id_categoria": 2,
            "valor_unitario": "55.0"
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.NOT_FOUND

@pytest.mark.parametrize("campo", ["-2.00", "fsdssç"])
def test_atualizar_produto_preco_invalido_retorna_422(client, products, auth_header_funcionario, campo):
    response = client.patch(
        url="/products/5",
        json={
            "nome": "Novo Produto",
            "id_categoria": 2,
            "valor_unitario": campo
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


#PATCH /produtos/{id}/estoque
def test_ajustar_estoque_como_funcionario_retorna_200(client, products, auth_header_funcionario):
    response = client.patch(
        url="/products/4/estoque",
        json={
            "estoque": 24
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

def test_ajustar_estoque_como_cliente_retorna_403(client, products, auth_header):
    response = client.patch(
        url="/products/4/estoque",
        json={
            "estoque": 24
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.FORBIDDEN

@pytest.mark.parametrize("campo", [-21, "fdkdsd"])
def test_ajustar_estoque_resultado_invalido_retorna_422(client, products, auth_header_funcionario, campo):
    response = client.patch(
        url="/products/4/estoque",
        json={
            "estoque": campo
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_ajustar_estoque_produto_inexistente_retorna_404(client, auth_header_funcionario):
    response = client.patch(
        url="/products/4/estoque",
        json={
            "estoque": 24
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
