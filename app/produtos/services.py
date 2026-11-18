from dataclasses import dataclass, field
from fastapi import HTTPException
from http import HTTPStatus

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.produtos.repository import ProdutoRepository
from app.categorias.repository import CategoriaReporitory
from app.produtos.models import Produto
from app.produtos.schemas import ProdutoCreate, ProdutoPaginated, ProdutoUpdate

@dataclass
class ProdutoService:
    _db: Session
    _produto_repo: ProdutoRepository = field(init=False)
    _categoria_repo: CategoriaReporitory = field(init=False)

    def __post_init__(self):
        self._produto_repo = ProdutoRepository(
            self._db
        )
        self._categoria_repo = CategoriaReporitory(
            self._db
        )

    def listar_produtos(self, dados: ProdutoPaginated) -> dict[str, bool | str | list[Produto]]:
        produtos = self._produto_repo.listar_produtos(
            dados.limit,
            dados.offset,
            dados.categoria
        )

        if not produtos:
            return {
                "success": True,
                "message": "Nenhum produto encontrado.",
                "data": produtos
            }

        return {
            "success": True,
            "message": "Produtos encontrados.",
            "data": produtos
        }

    def buscar_produto_por_id(self, produto_id: int) -> dict[str, bool | str | Produto]:
        produto = self._produto_repo.buscar_por_id(
            produto_id
        )

        if produto is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Produto não encontrado."
            )

        return {
            "success": True,
            "message": f"Produto {produto.id} encontrado.",
            "data": produto
        }

    def criar_produto(self, dados: ProdutoCreate) -> dict[str, bool | str | Produto]:
        categoria = self._categoria_repo.buscar_por_id(
            dados.id_categoria
        )

        if categoria is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Categoria não encontrada."
            )

        try:
            novo_produto = self._produto_repo.criar_produto(
                dados.nome,
                categoria.id,
                dados.valor_unitario,
                dados.estoque
            )

            self._db.commit()

            return {
                "success": True,
                "message": f"Produto {novo_produto.id} adicionado.",
                "data": novo_produto
            }

        except IntegrityError:
            self._db.rollback()
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="Não foi possivel adicionar o produto."
            )

    def atualizar_produtos(self, produto_id: int, dados: ProdutoUpdate) -> dict[str, str | bool | Produto]:
        produto = self._produto_repo.buscar_por_id(
            produto_id
        )

        if produto is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Produto não encontrado."
            )

        dados_update = dados.model_dump(
            exclude_unset=True
        )

        if dados_update.get("id_categoria"):
            categoria = self._categoria_repo.buscar_por_id(
                dados.id_categoria
            )

            if categoria is None:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail="Categoria não encontrada."
                )

        try:
            self._produto_repo.atualizar_produto(
                produto,
                dados_update
            )

            self._db.commit()
            self._db.refresh(produto)

            return {
                "success": True,
                "message": f"Produto {produto.id} atualizado.",
                "data": produto
            }

        except IntegrityError:
            self._db.rollback()
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="Não foi possivel atualizar o produto."
            )

    def atualizar_estoque(self, produto_id: int, estoque: int) -> dict[str, str | bool | Produto]:
        produto = self._produto_repo.buscar_por_id(
            produto_id
        )

        if produto is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Produto não encontrado."
            )

        produto.estoque = estoque

        self._db.commit()
        self._db.refresh(produto)

        return {
            "success": True,
            "message": f"Estoque do produto {produto.id} atualizado.",
            "data": produto
        }
