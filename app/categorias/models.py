from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, Relationship

from app.core.database import Base

class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    nome: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True
    )


    produtos: Mapped[list["Produto"]] = Relationship(
        back_populates="categoria"
    )