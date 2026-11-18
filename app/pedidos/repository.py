from dataclasses import dataclass
from sqlalchemy import select, exists
from sqlalchemy.orm import Session, selectinload
from decimal import Decimal
from datetime import timedelta

from app.pedidos.models import Pedido, ProdutoPedido, StatusPedido
from app.pedidos.schemas import PedidosFilters, OrdenarPor
from app.produtos.models import Produto

@dataclass
class PedidosRepository:
    _db: Session

    def criar_pedido(self, id_user: int) -> Pedido:
        novo_pedido = Pedido(
            id_usuario=id_user
        )

        self._db.add(novo_pedido)
        self._db.flush()

        return novo_pedido
    
    def retonar_itens_do_pedido(self, pedido_id: int, bloqueio: bool=False) -> Pedido:
        stmt = (
            select(Pedido)
            .where(Pedido.id == pedido_id)
            .options(
                selectinload(Pedido.itens)
                .joinedload(ProdutoPedido.produto)
                .joinedload(Produto.categoria)
            )
        )

        if bloqueio:
            stmt = stmt.with_for_update()

        pedido = self._db.scalar(stmt)

        return pedido

    def retonar_pedidos_com_filtros(self, dados: PedidosFilters) -> Pedido:
        stmt = (
            select(Pedido)
            .options(
                selectinload(Pedido.itens)
                .joinedload(ProdutoPedido.produto)
                .joinedload(Produto.categoria)
            )
        )

        if dados.status is not None:
            stmt = stmt.where(Pedido.status == dados.status)

        if dados.id_funcionario is not None:
            stmt = stmt.where(Pedido.id_funcionario == dados.id_funcionario)

        if dados.sem_funcionario:
            stmt = stmt.where(Pedido.id_funcionario.is_(None))

        if dados.id_usuario is not None:
            stmt = stmt.where(Pedido.id_usuario == dados.id_usuario)

        if dados.dt_inicio is not None:
            stmt = stmt.where(Pedido.dt_criacao >= dados.dt_inicio)

        if dados.dt_fim is not None:
            stmt = stmt.where(Pedido.dt_criacao < dados.dt_fim + timedelta(days=1))

        COLUNAS_PERMITIDAS = {
            "criado_em": Pedido.dt_criacao,
            "total": Pedido.valor_total,
            "status": Pedido.status
        }

        coluna = COLUNAS_PERMITIDAS[dados.ordenar_por]
        ordem = coluna.desc() if dados.direcao == "desc" else coluna.asc()

        stmt = stmt.order_by(ordem, Pedido.id.desc()).limit(dados.limit).offset(dados.offset)
        pedidos = self._db.scalars(stmt).all()

        return pedidos

    def buscar_por_id(self, id_pedido: int) -> Pedido | None:
        return self._db.get(Pedido, id_pedido)

    def verificar_pedidos_pendentes(self, user_id: int) -> bool:
        stmt = (
            select(
                exists().where(
                    Pedido.id_usuario == user_id,
                    Pedido.status == StatusPedido.PENDENTE
                )
            )
        )
        existe = self._db.scalar(stmt)

        return existe

@dataclass
class ItensPedidosRepository:
    _db: Session

    def criar_itens_pedidos(
            self,
            id_pedido: int,
            id_produto: int,
            qtd_produto: int,
            vlr_uni: Decimal
    ) -> ProdutoPedido:
        item_pedido = ProdutoPedido(
            id_pedido=id_pedido,
            id_produto=id_produto,
            qtd_produto=qtd_produto,
            valor_unitario=vlr_uni
        )

        return item_pedido

