from sqlalchemy import select, exists
from sqlalchemy.orm import Session, selectinload

from dataclasses import dataclass
from app.users.models import Usuario, RoleEnum
from app.pedidos.models import Pedido, ProdutoPedido, StatusPedido
from app.produtos.models import Produto

@dataclass
class UserRepository:
    _db: Session

    def buscar_por_id(self, user_id: int) -> Usuario | None:
        return self._db.get(Usuario, user_id)

    def buscar_por_email(self, email: str) -> Usuario:
        smtm = select(Usuario).where(Usuario.email == email)
        return self._db.scalar(smtm)

    def adicionar_usuario(self, nome: str, email: str, hash_senha: str) -> Usuario:
        novo_user = Usuario(
            nome=nome,
            email=email,
            hash_senha=hash_senha
        )

        self._db.add(novo_user)
        self._db.flush()

        return novo_user

    def listar_usuarios(self, limit: int, offset: int, role: RoleEnum) -> list[Usuario] | None:
        stmt = (select(Usuario)
                .where(Usuario.role == role)
                .limit(limit)
                .offset(offset)
                )
        users = self._db.scalars(stmt).all()

        if not users:
            return None

        return users

    def atualizar_dados_user(self, user: Usuario, dados: dict) -> None:
        for chave, valor in dados.items():
            setattr(user, chave, valor)

    def alterar_role(self, user: Usuario, nova_role: RoleEnum) -> Usuario:
        user.role = nova_role
        return user

    def bloquear_registro_user(self, id_user: int) -> None:
        stmt = (
            select(1)
            .where(Usuario.id == id_user)
            .with_for_update()
        )
        self._db.execute(stmt).one_or_none()
        
        return None

    def verificar_se_admin_existe(self) -> bool:
        stmt = (
            select(
                exists()
                .where(Usuario.role == RoleEnum.ADMIN)
            )
        )
        existe = self._db.scalar(stmt)

        return existe