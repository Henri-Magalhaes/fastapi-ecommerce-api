import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from datetime import timedelta
from random import uniform, randint
from decimal import Decimal

from app.main import app
from app.core.database import Base
from app.core.database import get_db
from app.core.models_registry import Usuario, StatusPedido, Produto, Pedido, RoleEnum, Categoria
from app.core.security import hash_password, create_token, create_access_token

TEST_DATABASE_URL = "sqlite://"

@pytest.fixture
def test_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={
            "check_same_thread": False
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_engine):
    with Session(test_engine) as session:
        yield session

@pytest.fixture
def client(db_session):
    def get_test_session():
        yield db_session

    app.dependency_overrides[get_db] = get_test_session

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()

@pytest.fixture
def user_cliente(db_session):
    user = Usuario(
        nome="Novo Usuario",
        email="novousuario@gmail.com",
        hash_senha=hash_password("Teste123")
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user

@pytest.fixture
def token(client, user_cliente):
    response = client.post(
            url="/auth/login",
            data={
                "username": user_cliente.email,
                "password": "Teste123"
            }
        )

    data = response.json()

    return data["access_token"]

@pytest.fixture
def auth_header(token):
    return {
        "Authorization": f"Bearer {token}"
    }

@pytest.fixture
def invalid_auth_header():
    token = create_token(1, "access", "CLIENTE", timedelta(seconds=1))
    return {
        "Authorization": f"Bearer {token}"
    }

@pytest.fixture
def user_admin(db_session):
    admin = Usuario(
        nome="Novo Usuario",
        email="novoadmin@gmail.com",
        hash_senha=hash_password("Teste123"),
        role=RoleEnum.ADMIN
    )

    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    return admin

@pytest.fixture
def admin_token(client, user_admin):
    response = client.post(
            url="/auth/login",
            data={
                "username": user_admin.email,
                "password": "Teste123"
            }
        )
    
    data = response.json()
    
    return data["access_token"]

@pytest.fixture
def auth_header_admin(admin_token):
    return {
        "Authorization": f"Bearer {admin_token}"
    }

@pytest.fixture
def users_clientes(db_session):
    for i in range(10):
        user = Usuario(
            nome=f"User Teste {i + 1}",
            email=f"userteste{i + 1}@gmail.com",
            hash_senha=hash_password(f"TesteSenha{i + 1}")
        )

        db_session.add(user)
        db_session.commit()

@pytest.fixture
def user_funcionario(db_session):
    funcionario = Usuario(
        nome="Novo Usuario",
        email="novousuariofunc@gmail.com",
        hash_senha=hash_password("Teste123"),
        role=RoleEnum.FUNCIONARIO
    )

    db_session.add(funcionario)
    db_session.commit()
    db_session.refresh(funcionario)

    return funcionario

@pytest.fixture
def funcionario_token(client, user_funcionario):
    response = client.post(
            url="/auth/login",
            data={
                "username": user_funcionario.email,
                "password": "Teste123"
            }
        )
        
    data = response.json()

    return data["access_token"]

@pytest.fixture
def auth_header_funcionario(funcionario_token):
    return {
        "Authorization": f"Bearer {funcionario_token}"
    }

@pytest.fixture
def products(db_session):
    categorias_list = [
        Categoria(
            nome="ALIMENTO"
        ),
        Categoria(
            nome="ELETRONICO"
        )
    ]

    db_session.add_all(categorias_list)
    db_session.commit()

    produtos_list = []

    for i in range(1, 11):
        valor_bruto = uniform(1.0, 1000.0)
        valor_produto = Decimal(str(valor_bruto)).quantize(Decimal("0.01"))

        estoque_produto = randint(50, 1000)
        categoria_id = 1

        if i > 5:
            categoria_id = 2

        produto = Produto(
            id_categoria=categoria_id,
            nome=f"Produto {i}",
            valor_unitario=valor_produto,
            estoque=estoque_produto,
        )

        produtos_list.append(produto)

    db_session.add_all(produtos_list)
    db_session.commit()

@pytest.fixture
def funcionarios(db_session):
    func_list = []

    for i in range(1, 11):
        func = Usuario(
            nome=f"Funcionario {i}",
            email=f"funcionario{i}@gmail.com",
            hash_senha=hash_password(f"Teste12{i}"),
            role=RoleEnum.FUNCIONARIO
        )

        func_list.append(func)

    db_session.add_all(func_list)
    db_session.commit()

@pytest.fixture
def pedidos_test(client, auth_header, products, db_session):
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
    pedido.status = StatusPedido.FINALIZADO

    db_session.commit()

    response02 = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 8, "quantidade": 2},
                {"id": 4, "quantidade": 4},
                {"id": 1, "quantidade": 10}
            ]
        },
        headers=auth_header
    )

    user = Usuario(
        nome="Usuario Teste",
        email="teste02@gmail.com",
        hash_senha=hash_password("senhaTeste123")
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token_user = create_access_token(
        user.id,
        user.role
    )

    auth_header_user = {
        "Authorization": f"Bearer {token_user}"
    }

    response03 = client.post(
        url="/orders/",
        json={
            "produtos": [
                {"id": 1, "quantidade": 2},
                {"id": 2, "quantidade": 14},
            ]
        },
        headers=auth_header_user
    )

    return (auth_header, auth_header_user)