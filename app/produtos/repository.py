from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select, update, exists
from sqlalchemy.orm import Session, contains_eager

from app.produtos.models import Produto
from app.categorias.models import Categoria

@dataclass
class ProdutoRepository:
    _db: Session

    def buscar_por_id(self, produto_id: int, bloqueio: bool=False):
        stmt = (
            select(Produto)
            .where(Produto.id == produto_id)
        )

        if bloqueio:
            stmt = stmt.with_for_update()

        produto = self._db.scalar(stmt)

        return produto

    def listar_produtos(self, limit: int, offset: int, categoria: str) -> list[Produto]:
        stmt = (
            select(Produto)
            .join(Produto.categoria)
            .options(
                contains_eager(Produto.categoria)
            )
            .limit(limit)
            .offset(offset)
        )

        if categoria is not None:
           stmt = stmt.where(Categoria.nome == categoria)

        produtos = self._db.scalars(stmt).all()

        return produtos

    def criar_produto(self, nome: str, id_categoria: int, vlr_unitario: Decimal, estoque: int) -> Produto:
        novo_produto = Produto(
            nome=nome,
            id_categoria=id_categoria,
            valor_unitario=vlr_unitario,
            estoque=estoque
        )

        self._db.add(novo_produto)
        self._db.flush()

        return novo_produto

    def atualizar_produto(self, produto: Produto, dados: dict) -> None:
        for chave, valor in dados.items():
            setattr(produto, chave, valor)

    def diminuir_estoque(self, produto_id: int, qtd: int) -> Decimal:
        stmt = (
            update(Produto)
            .where(Produto.id == produto_id,
                   Produto.estoque >= qtd)
            .values(estoque=Produto.estoque - qtd)
            .returning(Produto.valor_unitario)
        )
        result = self._db.scalar(stmt)

        return result

    def aumentar_estoque(self, produto_id: int, qtd: int) -> bool:
        stmt = (
            update(Produto)
            .where(Produto.id == produto_id)
            .values(estoque=Produto.estoque + qtd)
        )
        result = self._db.execute(stmt)

        return result.rowcount > 0

    def verificar_existencia(self, produto_id: int) -> bool:
        stmt = (
            select(
                exists()
                .where(Produto.id == produto_id)
            )
        )
        result = self._db.scalar(stmt)

        return result