from sqlalchemy import String, DateTime, func, Enum as SQlEnum
from sqlalchemy.orm import Mapped, mapped_column, Relationship

from enum import Enum
from datetime import datetime

from app.core.database import Base

class RoleEnum(str, Enum):
    CLIENTE = "CLIENTE"
    FUNCIONARIO = "FUNCIONARIO"
    ADMIN = "ADMIN"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    nome: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        unique=True
    )

    hash_senha: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    role: Mapped[RoleEnum] = mapped_column(
        SQlEnum(RoleEnum),
        nullable=False,
        default=RoleEnum.CLIENTE
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


    pedidos: Mapped[list["Pedido"]] = Relationship(
        back_populates="usuario",
        foreign_keys="Pedido.id_usuario"
    )

    pedidos_atendidos: Mapped[list["Pedido"]] = Relationship(
        back_populates="funcionario",
        foreign_keys="Pedido.id_funcionario"
    )