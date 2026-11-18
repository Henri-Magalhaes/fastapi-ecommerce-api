import pytest
from http import HTTPStatus
from decimal import Decimal

from app.core.models_registry import Pedido, StatusPedido, ProdutoPedido, Produto

def test_criar_pedido_com_itens_validos_retorna_201(client, auth_header, products):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 3, "quantidade": 13},
                {"id": 10, "quantidade": 2},
                {"id": 1, "quantidade": 23}
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.CREATED

    data = response.json()["data"]

    assert data["id"] == 1
    assert len(data["itens"]) == 3

def test_criar_pedido_grava_id_usuario_do_token(client, auth_header, products, db_session):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 3, "quantidade": 13},
                {"id": 10, "quantidade": 2},
                {"id": 1, "quantidade": 23}
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.CREATED

    pedido = db_session.get(Pedido, 1)

    assert pedido.id_usuario == 1

def test_criar_pedido_nasce_com_status_pendente(client, auth_header, products, db_session):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 3, "quantidade": 13},
                {"id": 10, "quantidade": 2},
                {"id": 1, "quantidade": 23}
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.CREATED

    pedido = db_session.get(Pedido, 1)

    assert pedido.status == StatusPedido.PENDENTE

def test_criar_pedido_nasce_sem_funcionario(client, auth_header, products, db_session):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 3, "quantidade": 13},
                {"id": 10, "quantidade": 2},
                {"id": 1, "quantidade": 23}
            ]
        },
        headers=auth_header
    )

    pedido = db_session.get(Pedido, 1)

    assert pedido.id_funcionario is None

def test_criar_pedido_grava_itens_em_produto_pedidos(client, auth_header, products, db_session):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 1, "quantidade": 13},
                {"id": 2, "quantidade": 2},
                {"id": 3, "quantidade": 23}
            ]
        },
        headers=auth_header
    )

    pedido = db_session.get(Pedido, 1)
    itens = pedido.itens

    assert len(itens) == 3

    for i, item in enumerate(itens):
        assert item.id == i + 1

def test_criar_pedido_grava_valor_unitario_do_momento(client, auth_header, products, db_session):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 1, "quantidade": 13},
            ]
        },
        headers=auth_header
    )

    item = db_session.get(ProdutoPedido, 1)
    preco_no_pedido = item.valor_unitario
    produto_pedido = item.produto

    produto_pedido.valor_unitario = "34.90"

    db_session.commit()
    db_session.refresh(produto_pedido)

    assert item.valor_unitario == preco_no_pedido
    assert produto_pedido != preco_no_pedido

def test_criar_pedido_calcula_total_no_servidor(client, auth_header, db_session, products):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 1, "quantidade": 13},
                {"id": 2, "quantidade": 2}
            ]
        },
        headers=auth_header
    )

    pedido = db_session.get(Pedido, 1)

    produto01 = db_session.get(Produto, 1)
    produto02 = db_session.get(Produto, 2)

    valor_uni01 = produto01.valor_unitario
    valor_uni02 = produto02.valor_unitario

    valor_total = (valor_uni01 * 13) + (valor_uni02 * 2)

    assert pedido.valor_total == valor_total

def test_criar_pedido_da_baixa_no_estoque(client, auth_header, db_session, products):
    produto = db_session.get(Produto, 1)
    estoque_antes = produto.estoque

    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 1, "quantidade": 13},
                {"id": 2, "quantidade": 2}
            ]
        },
        headers=auth_header
    )

    db_session.refresh(produto)

    estoque_depois = produto.estoque
    estoque_atualizado = estoque_antes - 13

    assert estoque_antes != estoque_depois
    assert estoque_depois == estoque_atualizado

def test_criar_pedido_com_varios_produtos_da_baixa_em_todos(client, auth_header, db_session, products):
    produtos = []
    estoques_antes = []

    for i in range(2):
        produto = db_session.get(Produto, i + 1)

        produtos.append(produto)
        estoques_antes.append(produto.estoque)

    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 1, "quantidade": 13},
                {"id": 2, "quantidade": 2}
            ]
        },
        headers=auth_header
    )

    estoque_depois = []

    for prod in produtos:
        db_session.refresh(prod)
        estoque_depois.append(prod.estoque)

        for estoq in estoques_antes:
            assert prod.estoque != estoq

    assert estoque_depois[0] == (estoques_antes[0] - 13)
    assert estoque_depois[1] == (estoques_antes[1] - 2)

def test_criar_pedido_com_mesmo_produto_repetido_na_lista_retorna_422(client, auth_header, products):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 1, "quantidade": 13},
                {"id": 1, "quantidade": 2}
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    message = response.json()["detail"]

    assert message == "Não eh permitido produtos duplicados."

def test_criar_pedido_sem_token_retorna_401(client, products):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 1, "quantidade": 13},
                {"id": 1, "quantidade": 2}
            ]
        }
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

def test_criar_pedido_com_lista_vazia_retorna_422(client, auth_header):
    response = client.post(
        url="/orders/",
        json={
            "produtos": []
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_criar_pedido_sem_campo_id_retorna_422(client, auth_header):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"quantidade": 13},
                {"quantidade": 2}
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_criar_pedido_com_quantidade_zero_retorna_422(client, auth_header):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 1, "quantidade": 0},
                {"id": 1, "quantidade": 0}
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_criar_pedido_com_quantidade_negativa_retorna_422(client, auth_header):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 1, "quantidade": -123},
                {"id": 1, "quantidade": -12}
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_criar_pedido_com_quantidade_nao_inteira_retorna_422(client, auth_header):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 1, "quantidade": 6.99},
                {"id": 1, "quantidade": 12.5}
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

@pytest.mark.parametrize("campo", [None, "fdssd,sl"])
def test_criar_pedido_com_id_produto_invalido_retorna_422(client, auth_header, campo):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": campo, "quantidade": 6.99},
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_criar_pedido_com_quantidade_absurda_retorna_422(client, auth_header):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 1, "quantidade": 1000},
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_criar_pedido_com_produto_inexistente_retorna_404(client, auth_header):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 1, "quantidade": 12},
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.NOT_FOUND

    message = response.json()["detail"]

    assert message == "Produto 1 não encontrado."

def test_criar_pedido_com_produto_sem_estoque_retorna_409(client, auth_header, db_session, products):
    produto_sem_estoque = Produto(
        id_categoria=1,
        nome=f"Produto 11",
        valor_unitario="45.99",
        estoque=0,
    )

    db_session.add(produto_sem_estoque)
    db_session.commit()
    db_session.refresh(produto_sem_estoque)

    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 11, "quantidade": 12},
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.CONFLICT

def test_criar_pedido_com_estoque_insuficiente_retorna_409(client, auth_header, products, db_session):
    produto = Produto(
        id_categoria=1,
        nome=f"Produto 11",
        valor_unitario="45.99",
        estoque=1,
    )

    db_session.add(produto)
    db_session.commit()
    db_session.refresh(produto)


    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 11, "quantidade": 99},
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.CONFLICT

def test_criar_pedido_pedindo_exatamente_o_estoque_disponivel_funciona(client, auth_header, products, db_session):
    produto = Produto(
        id_categoria=1,
        nome=f"Produto 11",
        valor_unitario="45.99",
        estoque=20,
    )

    db_session.add(produto)
    db_session.commit()
    db_session.refresh(produto)


    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 11, "quantidade": 20},
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.CREATED

    db_session.refresh(produto)

    assert produto.estoque == 0

def test_falha_em_um_item_nao_cria_pedido(client, auth_header, products, db_session):
    produto = Produto(
        id_categoria=1,
        nome=f"Produto 11",
        valor_unitario="45.99",
        estoque=2,
    )

    db_session.add(produto)
    db_session.commit()
    db_session.refresh(produto)

    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 3, "quantidade": 13},
                {"id": 11, "quantidade": 25},
                {"id": 1, "quantidade": 23}
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.CONFLICT

    pedido = db_session.get(Pedido, 1)

    assert pedido is None

def test_falha_em_um_item_nao_altera_estoque_dos_outros(client, auth_header, products, db_session):
    produto = Produto(
        id_categoria=1,
        nome=f"Produto 11",
        valor_unitario="45.99",
        estoque=2,
    )

    db_session.add(produto)
    db_session.commit()
    db_session.refresh(produto)

    produto_com_estoque = db_session.get(Produto, 3)
    estoque_antes = produto_com_estoque.estoque

    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 3, "quantidade": 13},
                {"id": 11, "quantidade": 25}
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.CONFLICT

    db_session.refresh(produto_com_estoque)

    estoque_depois = produto_com_estoque.estoque
    
    assert estoque_antes == estoque_depois

def test_falha_em_um_item_nao_cria_linhas_em_produto_pedidos(client, auth_header, products, db_session):
    produto = Produto(
        id_categoria=1,
        nome=f"Produto 11",
        valor_unitario="45.99",
        estoque=2,
    )

    db_session.add(produto)
    db_session.commit()
    db_session.refresh(produto)

    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 3, "quantidade": 13},
                {"id": 11, "quantidade": 25}
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.CONFLICT

    pedido = db_session.get(Pedido, 1)

    assert pedido is None

def test_criar_pedido_ignora_valor_unitario_enviado_no_payload(client, auth_header, products, db_session):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 3, "quantidade": 13, "valor_unitario": "0.1"},
                {"id": 10, "quantidade": 25}
            ]
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.CREATED

    pedido = db_session.get(Pedido, 1)
    itens = pedido.itens

    assert itens[0].valor_unitario != "0.1"

def test_criar_pedido_ignora_total_enviado_no_payload(client, auth_header, products, db_session):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 3, "quantidade": 13},
                {"id": 10, "quantidade": 25}
            ],
            "valor_total": "0.50"
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.CREATED

    pedido = db_session.get(Pedido, 1)

    assert pedido.valor_total != "0.50"

def test_criar_pedido_ignora_id_usuario_enviado_no_payload(client, auth_header, auth_header_admin, products, db_session):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 3, "quantidade": 13},
                {"id": 10, "quantidade": 25}
            ],
            "id_usuario": 2
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.CREATED

    pedido = db_session.get(Pedido, 1)

    assert pedido.id_usuario == 1

def test_criar_pedido_ignora_id_funcionario_enviado_por_cliente(client, auth_header, auth_header_admin, products, db_session):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 3, "quantidade": 13},
                {"id": 10, "quantidade": 25}
            ],
            "id_funcionario": 2
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.CREATED

    pedido = db_session.get(Pedido, 1)

    assert pedido.id_funcionario is None

def test_criar_pedido_ignora_status_enviado_no_payload(client, auth_header, products, db_session):
    response = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 3, "quantidade": 13},
                {"id": 10, "quantidade": 25}
            ],
            "status": StatusPedido.FINALIZADO
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.CREATED

    pedido = db_session.get(Pedido, 1)

    assert pedido.status == StatusPedido.PENDENTE


#GET /pedidos
def test_listar_pedidos_como_cliente_retorna_so_os_proprios(client, pedidos_test):
    auth_header01 = pedidos_test[0]
    auth_header02 = pedidos_test[1]

    response = client.get(
        url="/orders/?limit=10&offset=0",
        headers=auth_header01
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert len(data) == 2

    response2 = client.get(
        url="/orders/?limit=10&offset=0",
        headers=auth_header02
    )

    assert response2.status_code == HTTPStatus.OK

    data02 = response2.json()["data"]

    assert len(data02) == 1

def test_listar_pedidos_como_funcionario_retorna_todos(client, pedidos_test, auth_header_funcionario):
    response = client.get(
        url="/orders/?limit=10&offset=0",
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert len(data) == 3

def test_listar_pedidos_como_admin_retorna_todos(client, pedidos_test, auth_header_admin):
    response = client.get(
        url="/orders/?limit=10&offset=0",
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert len(data) == 3

def test_listar_pedidos_sem_token_retorna_401(client, pedidos_test):
    response = client.get(
        url="/orders/?limit=10&offset=0",
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

def test_listar_pedidos_cliente_sem_pedidos_retorna_lista_vazia(client, auth_header):
    response = client.get(
        url="/orders/?limit=10&offset=0",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert not data

def test_listar_pedidos_paginacao_respeita_limit_e_offset(client, pedidos_test):
    auth_header = pedidos_test[0]

    response = client.get(
        url="/orders/?limit=10&offset=1",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert len(data) == 1

    response02 = client.get(
        url="/orders/?limit=1&offset=0",
        headers=auth_header
    )

    assert response02.status_code == HTTPStatus.OK

    data2 = response02.json()["data"]

    assert len(data2) == 1

@pytest.mark.parametrize("campo", [-12, "kdskdl", 101])
def test_listar_pedidos_com_limit_invalido_retorna_422(client, auth_header, campo):
    response = client.get(
        url=f"/orders/?limit={campo}&offset=0",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_listar_pedidos_filtra_por_status(client, pedidos_test):
    auth_header = pedidos_test[0]

    response = client.get(
        url=f"/orders/?limit=10&offset=0&status=FINALIZADO",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert len(data) == 1
    assert data[0]["status"] == StatusPedido.FINALIZADO

def test_listar_pedidos_com_status_invalido(client, pedidos_test):
    auth_header = pedidos_test[0]
    
    response = client.get(
        url=f"/orders/?limit=10&offset=0&status=PAGO",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_listar_pedidos_filtra_por_periodo(client, pedidos_test):
    auth_header = pedidos_test[0]
        
    response = client.get(
        url=f"/orders/?limit=10&offset=0&dt_inicio=2026-11-01&dt_fim=2026-11-30",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert len(data) == 2

def test_listar_pedidos_com_periodo_invertido_retorna_422(client, pedidos_test):
    auth_header = pedidos_test[0]
            
    response = client.get(
        url=f"/orders/?limit=10&offset=0&dt_inicio=2026-11-30&dt_fim=2026-11-01",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    message = response.json()["detail"]

    assert message == "data_inicio não pode ser maior que data_fim"

def test_listar_pedidos_filtra_por_id_usuario_como_admin(client, pedidos_test, auth_header_admin):
    response = client.get(
        url="/orders/?limit=10&offset=0&id_usuario=1",
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert len(data) == 2

    response02 = client.get(
        url="/orders/?limit=10&offset=0&id_usuario=2",
        headers=auth_header_admin
    )

    assert response02.status_code == HTTPStatus.OK

    data2 = response02.json()["data"]

    assert len(data2) == 1

def test_cliente_nao_consegue_ver_pedidos_de_outro_usando_filtro_id_usuario(client, pedidos_test):
    auth_header = pedidos_test[0]

    response = client.get(
        url="/orders/?limit=10&offset=0&id_usuario=2",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert len(data) == 2


#GET /pedidos/{id}
def test_buscar_pedido_proprio_retorna_200_com_itens(client, pedidos_test):
    auth_header = pedidos_test[0]

    response = client.get(
        url="/orders/1",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert len(data["itens"]) == 3

    produtos = ["Produto 1", "Produto 3", "Produto 10"]

    for i, item in enumerate(data["itens"]):
        assert item["produto"]["nome"] == produtos[i]

def test_buscar_pedido_retorna_total_e_valor_unitario_de_cada_item(client, pedidos_test):
    auth_header = pedidos_test[0]
    
    response = client.get(
        url="/orders/1",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert len(data["itens"]) == 3
    assert "valor_total" in data

    valor_total = data["valor_total"]
    soma = 0

    for item in data["itens"]:
        valor_unitario = Decimal(str(item["valor_unitario"]).replace(",", "."))
        qtd_produto = Decimal(str(item["qtd_produto"]).replace(",", "."))

        soma += (valor_unitario * qtd_produto)

    assert valor_total == str(soma)

def test_buscar_pedido_de_outro_cliente_retorna_403_ou_404(client, pedidos_test):
    auth_header = pedidos_test[0]
        
    response = client.get(
        url="/orders/3",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.FORBIDDEN

    message = response.json()["detail"]

    assert message == "Ação não permitida."

def test_buscar_pedido_como_funcionario_retorna_200(client, pedidos_test, auth_header_funcionario):
    response = client.get(
        url="/orders/3",
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert len(data["itens"]) == 2

    produtos = ["Produto 1", "Produto 2"]

    for i, item in enumerate(data["itens"]):
        assert item["produto"]["nome"] == produtos[i]

def test_buscar_pedido_como_admin_retorna_200(client, pedidos_test, auth_header_admin):
    response = client.get(
        url="/orders/3",
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()["data"]

    assert len(data["itens"]) == 2

    produtos = ["Produto 1", "Produto 2"]

    for i, item in enumerate(data["itens"]):
        assert item["produto"]["nome"] == produtos[i]

def test_buscar_pedido_inexistente_retorna_404(client, pedidos_test):
    auth_header = pedidos_test[0]

    response = client.get(
        url="/orders/12",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.NOT_FOUND

    message = response.json()["detail"]

    assert message == "Pedido não encontrado."

def test_buscar_pedido_sem_token_retorna_401(client, pedidos_test):
    response = client.get(
        url="/orders/12",
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

@pytest.mark.parametrize("campo", ["smfksd", -219])
def test_buscar_pedido_com_id_invalido_retorna_422(client, pedidos_test, campo):
    auth_header = pedidos_test[0]

    response = client.get(
        url=f"/orders/{campo}",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_alterar_status_sem_token_retorna_401(client, pedidos_test):
    response = client.patch(
        url="/orders/2/status",
        json={
            "status": StatusPedido.FINALIZADO
        }
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

def test_alterar_status_como_funcionario_retorna_200(client, pedidos_test, auth_header_funcionario, db_session):
    response = client.patch(
        url="/orders/2/status",
        json={
            "status": StatusPedido.FINALIZADO
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

    pedido = db_session.get(Pedido, 2)

    assert pedido.status == StatusPedido.FINALIZADO

def test_alterar_status_como_admin_retorna_200(client, pedidos_test, auth_header_admin, db_session):
    response = client.patch(
        url="/orders/2/status",
        json={
            "status": StatusPedido.FINALIZADO
        },
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.OK

    pedido = db_session.get(Pedido, 2)

    assert pedido.status == StatusPedido.FINALIZADO

def test_alterar_status_como_cliente_retorna_403(client, pedidos_test, db_session):
    auth_header = pedidos_test[0]

    response = client.patch(
        url="/orders/2/status",
        json={
            "status": StatusPedido.FINALIZADO
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.FORBIDDEN

def test_alterar_status_de_pedido_inexistente_retorna_404(client, pedidos_test, auth_header_funcionario):
    response = client.patch(
        url="/orders/8/status",
        json={
            "status": StatusPedido.FINALIZADO
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.NOT_FOUND

    message = response.json()["detail"]

    assert message == "Pedido não encontrado."

def test_status_pendente_para_finalizado_permitido(client, pedidos_test, auth_header_funcionario):
    response = client.patch(
        url="/orders/2/status",
        json={
            "status": StatusPedido.FINALIZADO
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

def test_status_finalizado_para_pendente_retorna_409(client, pedidos_test, auth_header_funcionario):
    response = client.patch(
        url="/orders/1/status",
        json={
            "status": StatusPedido.PENDENTE
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.CONFLICT

    message = response.json()["detail"]

    assert message == f"Não é possível ir de {StatusPedido.FINALIZADO} para {StatusPedido.PENDENTE}"

def test_status_finalizado_para_cancelado_retorna_409(client, pedidos_test, auth_header_funcionario):
    response = client.patch(
        url="/orders/1/status",
        json={
            "status": StatusPedido.CANCELADO
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.CONFLICT

    message = response.json()["detail"]
    
    assert message == f"Não é possível ir de {StatusPedido.FINALIZADO} para {StatusPedido.CANCELADO}"

def test_status_de_pedido_finalizado_nao_muda_mais(client, pedidos_test, auth_header_funcionario, db_session):
    response = client.patch(
        url="/orders/1/status",
        json={
            "status": StatusPedido.CANCELADO
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.CONFLICT

    pedido = db_session.get(Pedido, 1)

    assert pedido.status == StatusPedido.FINALIZADO

def test_status_de_pedido_cancelado_nao_muda_mais(client, pedidos_test, auth_header_funcionario, db_session):
    pedido = db_session.get(Pedido, 1)
    pedido.status = StatusPedido.CANCELADO

    db_session.commit()

    response = client.patch(
        url="/orders/1/status",
        json={
            "status": StatusPedido.CANCELADO
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.CONFLICT

    db_session.refresh(pedido)

    assert pedido.status == StatusPedido.CANCELADO

def test_status_para_o_mesmo_status_atual_retorna_409(client, pedidos_test, auth_header_funcionario, db_session):
    response = client.patch(
        url="/orders/2/status",
        json={
            "status": StatusPedido.PENDENTE
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.CONFLICT

    pedido = db_session.get(Pedido, 2)

    assert pedido.status == StatusPedido.PENDENTE

def test_status_com_valor_invalido_retorna_422(client, pedidos_test, auth_header_funcionario):
    response = client.patch(
        url="/orders/2/status",
        json={
            "status": "PAGO"
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_finalizar_nao_mexe_no_estoque(client, pedidos_test, auth_header_funcionario, db_session):
    produto = db_session.get(Produto, 8)
    estoque_antes = produto.estoque

    response = client.patch(
        url="/orders/2/status",
        json={
            "status": StatusPedido.FINALIZADO
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

    db_session.refresh(produto)
    estoque_depois = produto.estoque

    assert estoque_antes == estoque_depois


#PATCH /pedidos/{id}/cancelar
def test_cancelar_pedido_proprio_pendente_retorna_200(client, pedidos_test, db_session):
    auth_header = pedidos_test[0]

    response = client.patch(
        url="/orders/2/cancelar",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.OK

def test_cancelar_muda_status_para_cancelado(client, pedidos_test, db_session):
    auth_header = pedidos_test[0]
    
    response = client.patch(
        url="/orders/2/cancelar",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.OK

    pedido = db_session.get(Pedido, 2)

    assert pedido.status == StatusPedido.CANCELADO

def test_cancelar_devolve_estoque_de_todos_os_itens(client, pedidos_test, db_session):
    auth_header = pedidos_test[0]

    produto = db_session.get(Produto, 4)
    estoque_antes = produto.estoque

    response = client.patch(
        url="/orders/2/cancelar",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.OK

    db_session.refresh(produto)
    estoque_depois = produto.estoque

    assert estoque_antes != estoque_depois
    assert estoque_depois == (estoque_antes + 4)

def test_cancelar_pedido_de_outro_cliente_retorna_403_ou_404(client, pedidos_test, db_session):
    auth_header = pedidos_test[0]

    response = client.patch(
        url="/orders/3/cancelar",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.FORBIDDEN

    message = response.json()["detail"]

    assert message == "Ação não permitida."

    pedido = db_session.get(Pedido, 3)

    assert pedido.status != StatusPedido.CANCELADO
    assert pedido.status == StatusPedido.PENDENTE

def test_cancelar_pedido_ja_cancelado_retorna_409(client, pedidos_test, db_session):
    auth_header = pedidos_test[0]
    
    response = client.patch(
        url="/orders/2/cancelar",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.OK

    produto = db_session.get(Produto, 4)
    estoque_antes = produto.estoque

    response2 = client.patch(
        url="/orders/2/cancelar",
        headers=auth_header
    )

    assert response2.status_code == HTTPStatus.CONFLICT

    message = response2.json()["detail"]

    assert message == "Pedido 2 não pode ser cancelado."

    db_session.refresh(produto)
    estoque_depois = produto.estoque

    assert estoque_antes == estoque_depois

def test_cancelar_pedido_inexistente_retorna_404(client, pedidos_test):
    auth_header = pedidos_test[0]
        
    response = client.patch(
        url="/orders/19/cancelar",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.NOT_FOUND

def test_cancelar_sem_token_retorna_401(client, pedidos_test):
    response = client.patch(
        url="/orders/19/cancelar"
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

def test_cancelar_pedido_finalizado_como_cliente(client, pedidos_test):
    auth_header = pedidos_test[0]
            
    response = client.patch(
        url="/orders/1/cancelar",
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.CONFLICT

    message = response.json()["detail"]

    assert message == "Pedido 1 não pode ser cancelado."

def test_cancelar_como_funcionario_retorna_200(client, pedidos_test, auth_header_funcionario):
    response = client.patch(
        url="/orders/2/cancelar",
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

def test_cancelar_como_admin_retorna_200(client, pedidos_test, auth_header_admin):
    response = client.patch(
        url="/orders/2/cancelar",
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.OK


#PATCH /pedidos/{id}/funcionario
def test_atribuir_funcionario_como_funcionario_retorna_200(client, auth_header_funcionario, pedidos_test):
    response = client.patch(
        url="/orders/2/funcionario",
        json={
            "id_func": 1
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

def test_atribuir_funcionario_persiste_no_banco(client, auth_header_funcionario, pedidos_test, db_session):
    response = client.patch(
        url="/orders/2/funcionario",
        json={
            "id_func": 1
        },
        headers=auth_header_funcionario
    )

    assert response.status_code == HTTPStatus.OK

    pedido = db_session.get(Pedido, 2)

    assert pedido.id_funcionario is not None
    assert pedido.id_funcionario == 1

def test_atribuir_funcionario_como_admin_retorna_200(client, auth_header_funcionario, auth_header_admin, pedidos_test):
    response = client.patch(
        url="/orders/2/funcionario",
        json={
            "id_func": 1
        },
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.OK

def test_atribuir_funcionario_como_cliente_retorna_403(client, pedidos_test):
    auth_header = pedidos_test[0]

    response = client.patch(
        url="/orders/2/funcionario",
        json={
            "id_func": 1
        },
        headers=auth_header
    )

    assert response.status_code == HTTPStatus.FORBIDDEN

def test_atribuir_funcionario_sem_token_retorna_401(client, pedidos_test):
    response = client.patch(
        url="/orders/2/funcionario",
        json={
            "id_func": 1
        }
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

def test_atribuir_usuario_que_nao_e_funcionario_retorna_404(client, pedidos_test, auth_header_admin):
    response = client.patch(
        url="/orders/2/funcionario",
        json={
            "id_func": 1
        },
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.NOT_FOUND

    message = response.json()["detail"]

    assert message == "Funcionario não encontrado."

def test_atribuir_funcionario_inexistente_retorna_404(client, pedidos_test, auth_header_admin):
    response = client.patch(
        url="/orders/2/funcionario",
        json={
            "id_func": 13
        },
        headers=auth_header_admin
    )

    assert response.status_code == HTTPStatus.NOT_FOUND

    message = response.json()["detail"]

    assert message == "Funcionario não encontrado."

