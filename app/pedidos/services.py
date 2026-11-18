from dataclasses import dataclass, field
from fastapi import HTTPException
from http import HTTPStatus

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.models_registry import Usuario, Pedido, RoleEnum
from app.pedidos.models import StatusPedido
from app.pedidos.repository import PedidosRepository, ItensPedidosRepository
from app.produtos.repository import ProdutoRepository
from app.pedidos.schemas import PedidoCreate, PedidosFilters
from app.users.repository import UserRepository

@dataclass
class PedidosService:
    _db: Session
    _pedidos_repo: PedidosRepository = field(init=False)
    _itens_pedido_repo: ItensPedidosRepository = field(init=False)
    _produto_repo: ProdutoRepository = field(init=False)
    _user_repo: UserRepository = field(init=False)

    def __post_init__(self):
        self._pedidos_repo = PedidosRepository(
            self._db
        )
        self._itens_pedido_repo = ItensPedidosRepository(
            self._db
        )
        self._produto_repo = ProdutoRepository(
            self._db
        )
        self._user_repo = UserRepository(
            self._db
        )

    def criar_pedido(
            self,
            user_atual: Usuario,
            lista_produtos: PedidoCreate
    ) -> dict[str, bool | str | Pedido]:
        if not lista_produtos.produtos:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="Não eh possivel criar o pedido sem produtos."
            )
        
        id_produtos = {}
        
        for pr in lista_produtos.produtos:
            if pr.id in id_produtos:
                raise HTTPException(
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                    detail="Não eh permitido produtos duplicados."
                )

            id_produtos[pr.id] = pr.quantidade

        ids_ordenados = dict(sorted(id_produtos.items()))

        try:
            self._user_repo.bloquear_registro_user(
                user_atual.id
            )

            if self._pedidos_repo.verificar_pedidos_pendentes(user_atual.id):
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail="O usuário possui pedidos pendentes."
                )

            pedido = self._pedidos_repo.criar_pedido(
                user_atual.id
            )

            itens_pedido_list = []
            vlr_total = 0

            for id, quantidade in ids_ordenados.items():
                valor_a_pagar = self._produto_repo.diminuir_estoque(
                    id,
                    quantidade
                )

                if valor_a_pagar is None:
                    if not self._produto_repo.verificar_existencia(id):
                        raise HTTPException(
                            status_code=HTTPStatus.NOT_FOUND,
                            detail=f"Produto {id} não encontrado."
                        )
                    
                    else:
                        raise HTTPException(
                            status_code=HTTPStatus.CONFLICT,
                            detail=f"Estoque insuficiente para o produto {id}"
                        )

                item_pedido = self._itens_pedido_repo.criar_itens_pedidos(
                    pedido.id,
                    id,
                    quantidade,
                    valor_a_pagar
                )

                vlr_total += (valor_a_pagar * quantidade)

                itens_pedido_list.append(item_pedido)

            pedido.valor_total = vlr_total

            self._db.add_all(itens_pedido_list)
            self._db.commit()

            dados_pedido = self._pedidos_repo.retonar_itens_do_pedido(
                pedido.id,
                True
            )

            return {
                "success": True,
                "message": f"Pedido {pedido.id} criado.",
                "data": dados_pedido
            }

        except IntegrityError:
            self._db.rollback()
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="Não foi possivel criar o pedido."
            )
        
        except Exception:
            self._db.rollback()
            raise

    def mostrar_pedidos(self, user_atual: Usuario, dados: PedidosFilters) -> dict[str, bool | str | Pedido]:
        if user_atual.role == RoleEnum.CLIENTE:
            if dados.id_funcionario is not None or dados.sem_funcionario:
                raise HTTPException(
                    status_code=HTTPStatus.FORBIDDEN,
                    detail="Filtro não permitido para clientes."
                )

            dados.id_usuario = user_atual.id

        if dados.sem_funcionario and dados.id_funcionario is not None:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="sem_funcionario e id_funcionario são contraditórios"
            )

        if dados.dt_inicio and dados.dt_fim and dados.dt_inicio > dados.dt_fim:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="data_inicio não pode ser maior que data_fim"
            )

        pedidos = self._pedidos_repo.retonar_pedidos_com_filtros(
            dados
        )

        if not pedidos:
            return {
                "success": True,
                "message": "Pedidos não encontrados.",
                "data": pedidos
            }

        return {
            "success": True,
            "message": "Pedidos encontrados.",
            "data": pedidos
        }

    def buscar_pedido_por_id(self, user_atual: Usuario, pedido_id: int) -> dict[str, bool | str | Pedido]:
        pedido = self._pedidos_repo.buscar_por_id(
            pedido_id
        )

        if pedido is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Pedido não encontrado."
            )

        if user_atual.role == RoleEnum.CLIENTE:
            if pedido.id_usuario != user_atual.id:
                raise HTTPException(
                    status_code=HTTPStatus.FORBIDDEN,
                    detail="Ação não permitida."
                )

        dados_pedido = self._pedidos_repo.retonar_itens_do_pedido(
            pedido.id
        )

        return {
            "success": True,
            "message": f"Pedido {pedido.id} encontrado.",
            "data": dados_pedido
        }

    def alterar_status(self, id_pedido: int, status: StatusPedido) -> dict[str, bool | str | Pedido]:
        pedido = self._pedidos_repo.retonar_itens_do_pedido(
            id_pedido,
            True
        )

        if pedido is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Pedido não encontrado."
            )

        TRANSICAO = {
            "PENDENTE": {StatusPedido.FINALIZADO},
            "FINALIZADO": set(),
            "CANCELADO": set()
        }

        if status not in TRANSICAO[pedido.status]:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail=f"Não é possível ir de {pedido.status} para {status}"
            )

        pedido.status = status

        self._db.commit()
        self._db.refresh(pedido)

        return {
            "success": True,
            "message": f"Status do pedido {pedido.id} atualizado.",
            "data": pedido
        }

    def cancelar_pedido(self, id_pedido: int, user_atual: Usuario) -> dict[str, bool | str | Pedido]:
        pedido = self._pedidos_repo.retonar_itens_do_pedido(
            id_pedido,
            True
        )

        if pedido is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Pedido não encontrado."
            )

        if user_atual.role == RoleEnum.CLIENTE:
            if pedido.id_usuario != user_atual.id:
                raise HTTPException(
                    status_code=HTTPStatus.FORBIDDEN,
                    detail="Ação não permitida."
                )

        if pedido.status != StatusPedido.PENDENTE:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail=f"Pedido {pedido.id} não pode ser cancelado."
            )

        try:
            itens_pedido = pedido.itens
            ids_produto = {}

            for item in itens_pedido:
                if not item.id_produto in ids_produto:
                    ids_produto[item.id_produto] = item.qtd_produto

            ids_ordenados = dict(sorted(ids_produto.items()))

            for id, quantidade in ids_ordenados.items():
                produto_alterado = self._produto_repo.aumentar_estoque(
                    id,
                    quantidade
                )

                if not produto_alterado:
                    raise HTTPException(
                        status_code=HTTPStatus.NOT_FOUND,
                        detail="Produto não encontrado."
                    )

            pedido.status = StatusPedido.CANCELADO

            self._db.commit()
            self._db.refresh(pedido)

            return {
                "success": True,
                "message": f"Pedido {pedido.id} cancelado.",
                "data": pedido
            }

        except Exception:
            self._db.rollback()
            raise

    def atribuir_func(self, id_pedido: int, func_atual: Usuario, id_func: int):
        pedido = self._pedidos_repo.retonar_itens_do_pedido(
            id_pedido,
            True
        )

        if pedido is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Pedido não encontrado."
            )

        if func_atual.role == RoleEnum.FUNCIONARIO:
            if pedido.id_funcionario is not None:
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail=f"Pedido {pedido.id} já tem um funcionario atribuido."
                )

            id_func = func_atual.id

        else:
            func = self._db.get(Usuario, id_func)

            if func is None:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail="Funcionario não encontrado."
                )

            if func.role != RoleEnum.FUNCIONARIO:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail="Funcionario não encontrado."
                )

        pedido.id_funcionario = id_func

        self._db.commit()
        self._db.refresh(pedido)

        return {
            "success": True,
            "message": f"Funcionario atribuido no pedido {pedido.id}.",
            "data": pedido
        }    