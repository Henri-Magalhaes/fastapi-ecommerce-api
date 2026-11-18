E-commerce API

API REST de e-commerce construída com FastAPI, SQLAlchemy 2 e PostgreSQL. O projeto cobre autenticação com JWT, controle de acesso por papéis (cliente, funcionário e admin), catálogo de produtos e categorias, e um fluxo de pedidos com controle de estoque seguro contra requisições simultâneas.

Projeto de estudo e portfólio.

Destaques
Autenticação e autorização: login com JWT, senhas com Argon2 e três papéis (CLIENTE, FUNCIONARIO, ADMIN).
Estoque sem venda em excesso: o estoque é baixado de forma atômica no banco, então pedidos simultâneos não vendem mais do que existe. O cancelamento devolve o estoque.
Pedidos consistentes: o preço do produto é registrado no item no momento da compra, e o pedido é tudo-ou-nada (se um item falha, nada é gravado).
Concorrência tratada: itens são processados em ordem fixa para evitar deadlock, e cancelamento e finalização usam trava de linha para não conflitarem.
Arquitetura em camadas: rotas, services, repositories e models separados por módulo.
Migrações com Alembic e testes automatizados com pytest.
Stack
Área	Tecnologia
Framework	FastAPI
Banco de dados	PostgreSQL
ORM e migrações	SQLAlchemy 2 e Alembic
Validação e configuração	Pydantic v2 e pydantic-settings
Autenticação	PyJWT e Argon2
Testes	pytest
Gerenciador de dependências	uv
Como rodar
Pré-requisitos
Python 3.14 ou superior (conforme o pyproject.toml)
uv
Um banco PostgreSQL acessível
Passo a passo
bash
# 1. Clone o repositório
git clone https://github.com/Henri-Magalhaes/fastapi-ecommerce-api.git
cd fastapi-ecommerce-api

# 2. Instale as dependências
uv sync

# 3. Configure as variáveis de ambiente
cp .env.example .env
# edite o .env com a URL do seu banco e uma SECRET_KEY própria

# 4. Aplique as migrações
uv run alembic upgrade head

# 5. Suba a API
uv run uvicorn app.main:app --reload

A documentação interativa fica em http://localhost:8000/docs.

Se você não tem um PostgreSQL local, uma forma rápida de subir um é com Docker:

bash
docker run --name ecommerce-db -e POSTGRES_USER=usuario -e POSTGRES_PASSWORD=senha \
  -e POSTGRES_DB=ecommerce -p 5432:5432 -d postgres:17
Variáveis de ambiente
Variável	Descrição
DATABASE_URL	URL de conexão do SQLAlchemy, por exemplo postgresql+psycopg://usuario:senha@localhost:5432/ecommerce
SECRET_KEY	Chave usada para assinar os tokens JWT. Gere uma com python -c "import secrets; print(secrets.token_urlsafe(64))"
ALGORITHM	Algoritmo do JWT (HS256)
ACCESS_TOKEN_TIME	Validade do token de acesso, em minutos
Criando o primeiro admin

Todo cadastro feito pela API nasce como CLIENTE. O primeiro admin é criado por um script interativo, que pergunta nome, email e senha (a senha não aparece no terminal):

bash
uv run python -m app.scripts.criar_admin

Rode o comando a partir da raiz do projeto, depois de aplicar as migrações. O script só cria o admin se ainda não existir nenhum no banco. A partir daí, o admin pode alterar o papel de outros usuários pela API (PATCH /users/{id}/role).

Testes
bash
uv run pytest

Os testes usam SQLite em memória, mas a aplicação lê as variáveis de ambiente ao ser importada, então o .env precisa existir.

Papéis e permissões
Ação	Cliente	Funcionário	Admin
Cadastrar, fazer login e ver o próprio perfil	sim	sim	sim
Listar produtos e categorias	sim	sim	sim
Criar e editar produtos, ajustar estoque	não	sim	sim
Criar, editar e remover categorias	não	sim	sim
Criar pedido	sim	sim	sim
Ver pedidos	só os próprios	todos	todos
Cancelar pedido	só os próprios	qualquer	qualquer
Finalizar pedido	não	sim	sim
Atribuir funcionário a um pedido	não	a si mesmo	qualquer funcionário
Listar usuários	não	só clientes	todos
Ver usuário por id	só o próprio	só clientes	todos
Alterar o papel de um usuário	não	não	sim
Endpoints
Método	Rota	Acesso
GET	/health	público
POST	/auth/register	público
POST	/auth/login	público (formulário OAuth2: username é o email)
GET	/auth/me	autenticado
GET	/users/	funcionário ou admin
GET	/users/{user_id}	autenticado (conforme o papel)
PATCH	/users/me	autenticado
PATCH	/users/{user_id}/role	admin
GET	/categories/	público
GET	/categories/{id_categoria}	público
POST	/categories/	funcionário ou admin
PATCH	/categories/{id_categoria}	funcionário ou admin
DELETE	/categories/{id_categoria}	funcionário ou admin
GET	/products/	público (filtro por categoria e paginação)
GET	/products/{produto_id}	público
POST	/products/	funcionário ou admin
PATCH	/products/{produto_id}	funcionário ou admin
PATCH	/products/{produto_id}/estoque	funcionário ou admin
POST	/orders/	autenticado
GET	/orders/	autenticado (com filtros)
GET	/orders/{id_pedido}	autenticado (conforme o papel)
PATCH	/orders/{id_pedido}/status	funcionário ou admin
PATCH	/orders/{id_pedido}/cancelar	autenticado (conforme o papel)
PATCH	/orders/{id_pedido}/funcionario	funcionário ou admin

As rotas protegidas usam o token no cabeçalho Authorization: Bearer <token>. As listagens aceitam limit e offset, e a listagem de pedidos também aceita filtros por funcionário, cliente, status e período.

Regras de negócio
Pedidos
Um pedido precisa ter pelo menos um item, e o mesmo produto não pode aparecer duas vezes.
Cada item aceita de 1 a 99 unidades.
Cada cliente pode ter um pedido pendente por vez.
O preço unitário é copiado para o item no momento da compra, então mudar o preço do produto depois não altera pedidos antigos.
Se qualquer item não tiver estoque suficiente, o pedido inteiro é recusado com 409 e nenhum estoque é alterado.
Fluxo de status
PENDENTE ──(funcionário/admin: PATCH /status)──> FINALIZADO
    │
    └──(PATCH /cancelar)──────────────────────> CANCELADO

FINALIZADO e CANCELADO são estados finais. O cancelamento devolve ao estoque a quantidade de cada item.

Estoque e concorrência
A baixa de estoque é um único comando no banco, que só decrementa se houver quantidade suficiente. Isso impede que duas requisições simultâneas vendam a mesma unidade.
Os itens de um pedido são processados em ordem crescente de id de produto, para que pedidos concorrentes não gerem deadlock.
Cancelar e finalizar o mesmo pedido ao mesmo tempo é serializado com trava de linha: só uma das ações vence.
Estas garantias foram verificadas em um PostgreSQL real com requisições simultâneas (disputa de estoque, cancelamento duplo, cancelar contra finalizar e ordens opostas de itens).
Formato das respostas

Respostas de sucesso seguem um envelope padrão:

json
{
  "success": true,
  "message": "...",
  "data": {}
}

Erros usam o formato padrão do FastAPI, com o campo detail.

Estrutura do projeto
app/
├── autenticacao/   # registro, login e token
├── users/          # usuários e papéis
├── categorias/     # categorias de produtos
├── produtos/       # catálogo e estoque
├── pedidos/        # pedidos e itens
├── core/           # configuração, banco, segurança e dependências
├── scripts/        # scripts utilitários (criação do primeiro admin)
└── main.py
migrations/         # migrações do Alembic
tests/              # testes automatizados

Cada módulo segue a mesma divisão: routes (HTTP), services (regras de negócio), repository (acesso ao banco), models (tabelas) e schemas (validação e respostas).

Próximos passos
[ ] Docker e docker-compose (API e PostgreSQL)
[ ] Integração contínua com GitHub Actions
[ ] Testes de concorrência rodando em PostgreSQL
[x] Script para criar o primeiro admin
[ ] Preço e estoque na resposta de produtos
[ ] Limites de valor para preço e estoque
