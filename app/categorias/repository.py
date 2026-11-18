from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.categorias.models import Categoria
from app.categorias.schemas import CategoriaFilter

@dataclass
class CategoriaReporitory:
    _db: Session

    def buscar_por_id(self, id_categoria: int) -> Categoria | None:
        return self._db.get(
            Categoria,
            id_categoria
        )

    def buscar_por_nome(self, nome: str) -> Categoria | None:
        stmt = (
            select(Categoria)
            .where(Categoria.nome == nome)
        )
        categoria = self._db.scalar(stmt)

        return categoria

    def listar_categorias(self, dados: CategoriaFilter) -> list[Categoria]:
        stmt = (
            select(Categoria)
            .limit(dados.limit)
            .offset(dados.offset)
        )
        categorias = self._db.scalars(stmt).all()

        return categorias

    def criar_categoria(self, nome: str) -> Categoria:
        nova_categoria = Categoria(
            nome=nome
        )

        self._db.add(nova_categoria)
        self._db.flush()

        return nova_categoria

    def deletar_categoria(self, categoria: Categoria):
        self._db.delete(categoria)
        return categoria