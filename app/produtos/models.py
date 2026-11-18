from sqlalchemy import String, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, Relationship

from decimal import Decimal

from app.core.database import Base

class Produto(Base):
    __tablename__ = "produtos"

    __table_args__ = (
        CheckConstraint(
            "valor_unitario >= 0",
            name="vlr_unitario_positivo"
        ),

        CheckConstraint(
            "estoque >= 0",
            name="estoque_positivo"
        )
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    id_categoria: Mapped[int] = mapped_column(
        ForeignKey("categorias.id",
                   ondelete="RESTRICT"),
        nullable=False
    )

    nome: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    valor_unitario: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    estoque: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )


    pedidos: Mapped[list["ProdutoPedido"]] = Relationship(
        back_populates="produto"
    )

    categoria: Mapped["Categoria"] = Relationship(
        back_populates="produtos"
    )