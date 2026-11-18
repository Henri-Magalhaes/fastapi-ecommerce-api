from dataclasses import dataclass, field
from fastapi import HTTPException
from http import HTTPStatus
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.categorias.repository import CategoriaReporitory
from app.categorias.schemas import CategoriaFilter

@dataclass
class CategoriaService:
    _db: Session
    _categoria_repo: CategoriaReporitory = field(init=False)

    def __post_init__(self):
        self._categoria_repo = CategoriaReporitory(self._db)

    def listar_categorias(self, dados: CategoriaFilter):
        categorias = self._categoria_repo.listar_categorias(
            dados
        )

        if not categorias:
            return {
                "success": True,
                "message": "Nenhuma categoria encontrada.",
                "data": categorias
            }

        return {
            "success": True,
            "message": "Categorias encontradas.",
            "data": categorias
        }

    def buscar_categoria_por_id(self, id_categoria: int):
        categoria = self._categoria_repo.buscar_por_id(
            id_categoria
        )

        if categoria is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Categoria não encontrada."
            )

        return {
            "success": True,
            "message": "Categoria encontrada.",
            "data": categoria
        }

    def criar_nova_categoria(self, nome: str):
        if self._categoria_repo.buscar_por_nome(nome) is not None:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="Não é possivel criar essa categoria."
            )


        try:
            nova_categoria = self._categoria_repo.criar_categoria(
                nome
            )

            self._db.commit()
            self._db.refresh(nova_categoria)

            return {
                "success": True,
                "message": f"Categoria {nova_categoria.id} criada.",
                "data": nova_categoria
            }

        except IntegrityError:
            self._db.rollback()
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="Não foi possivel criar essa categoria."
            )

    def atualizar_categoria(self, nome: str, id_categoria: int):
        categoria = self._categoria_repo.buscar_por_id(
            id_categoria
        )

        if categoria is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Categoria não encontrada."
            )

        if self._categoria_repo.buscar_por_nome(nome) is not None:
            if categoria.nome != nome:
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail="Não é possivel atualizar essa categoria."
                )

        try:
            categoria.nome = nome

            self._db.commit()
            self._db.refresh(categoria)

            return {
                "success": True,
                "message": f"Categoria {categoria.id} atualizada.",
                "data": categoria
            }

        except IntegrityError:
            self._db.rollback()
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="Não foi possivel atualizar a categoria."
            )

    def remover_categoria(self, id_categoria: int):
        categoria = self._categoria_repo.buscar_por_id(
            id_categoria
        )

        if categoria is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Categoria não encontrada."
            )

        try:
            self._categoria_repo.deletar_categoria(
                categoria
            )

            self._db.commit()

            return {
                "success": True,
                "message": f"Categoria {categoria.id} deletada.",
                "data": None
            }

        except IntegrityError:
            self._db.rollback()
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="Não foi possivel deletar essa categoria."
            )
            