from fastapi import FastAPI

from app.core import models_registry

from app.autenticacao.routes import auth_router
from app.users.routes import users_router
from app.produtos.routes import product_router
from app.pedidos.routes import order_router
from app.categorias.routes import category_router

app = FastAPI(title="ECOMMERCE API")

@app.get("/health")
async def heath():
    return {"status": "OK"}

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(product_router)
app.include_router(order_router)
app.include_router(category_router)