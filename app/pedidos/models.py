from sqlalchemy import Numeric, ForeignKey, DateTime, func, CheckConstraint, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, Relationship

from decimal import Decimal
from enum import Enum
from datetime import datetime

from app.core.database import Base

class StatusPedido(str, Enum):
    FINALIZADO = "FINALIZADO"
    CANCELADO = "CANCELADO"
    PENDENTE = "PENDENTE"


class Pedido(Base):
    __tablename__ = "pedidos"

    __table_args__ = (
        CheckConstraint(
            "valor_total >= 0",
            name="ck_valor_total_positivo"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    id_usuario: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id",
                   ondelete="RESTRICT"),
        nullable=False
    )

    id_funcionario: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id",
                   ondelete="SET NULL"),
        nullable=True
    )

    valor_total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    status: Mapped[StatusPedido] = mapped_column(
        SQLEnum(StatusPedido),
        nullable=False,
        default=StatusPedido.PENDENTE
    )

    dt_criacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    dt_atualizacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


    usuario: Mapped["Usuario"] = Relationship(
        back_populates="pedidos",
        foreign_keys=[id_usuario]
    )

    funcionario: Mapped["Usuario"] = Relationship(
        back_populates="pedidos_atendidos",
        foreign_keys=[id_funcionario]
    )

    itens: Mapped[list["ProdutoPedido"]] = Relationship(
        back_populates="pedido",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

class ProdutoPedido(Base):
    __tablename__ = "produto_pedidos"

    __table_args__ = (
        CheckConstraint(
            "qtd_produto > 0",
            name="ck_qtd_produto_positivo"
        ),

        CheckConstraint(
            "valor_unitario >= 0",
            name="ck_valor_unitario_positivo"
        ),

        UniqueConstraint(
            "id_pedido",
            "id_produto",
            name="uq_pedido_produto"
        )
    )


    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    id_pedido: Mapped[int] = mapped_column(
        ForeignKey("pedidos.id",
                   ondelete="CASCADE"),
        nullable=False
    )

    id_produto: Mapped[int] = mapped_column(
        ForeignKey("produtos.id",
                   ondelete="RESTRICT"),
        nullable=False
    )

    qtd_produto: Mapped[int] = mapped_column(
        nullable=False
    )

    valor_unitario: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )


    pedido: Mapped["Pedido"] = Relationship(
        back_populates="itens"
    )

    produto: Mapped["Produto"] = Relationship(
        back_populates="pedidos"
    )