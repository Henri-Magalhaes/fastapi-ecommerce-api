from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError
from getpass import getpass

from app.core.database import LocalSession
from app.autenticacao.schemas import RegisterInput
from app.users.repository import UserRepository
from app.core.security import hash_password
from app.core.models_registry import *


def input_personalizado(user_repo: UserRepository) -> RegisterInput:
    while True:
        try:
            nome = input("Digite seu nome: ")
            email = input("Digite seu email: ")
            senha = getpass("Digite a sua senha: ")
            confirmar_senha = getpass("Confirme a sua senha: ")

            if senha != confirmar_senha:
                print("As senhas não coincidem.")
                raise ValueError

            dados_validados = RegisterInput(
                nome=nome,
                email=email,
                senha=senha
            )

            if user_repo.buscar_por_email(dados_validados.email):
                print("Já existe um usuário com esse email!")
                raise ValueError

            return dados_validados
        
        except ValueError:
            continue

        except ValidationError:
            continue

def criar_primeiro_admin():
    with LocalSession() as session:
        user_repo = UserRepository(session)

        if user_repo.verificar_se_admin_existe():
            print("Já existe um admin no banco")
            return

        dados = input_personalizado(
            user_repo
        )
        senha_hash = hash_password(dados.senha)

        try:
            novo_admin = Usuario(
                nome=dados.nome,
                email=dados.email,
                hash_senha=senha_hash,
                role=RoleEnum.ADMIN
            )

            session.add(novo_admin)
            session.commit()

            print("Administrador criado com sucesso!")

        except IntegrityError:
            print('Ocorreu um erro de integridade, não foi possivel criar o admin')
            return

if __name__ == "__main__":
    criar_primeiro_admin()
