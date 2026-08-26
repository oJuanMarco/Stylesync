# 👗 StyleSync

> 🇧🇷 Português | [🇺🇸 English below](#-stylesync-1)

---

API REST em Python (Flask) com persistência em MongoDB para gestão de catálogo de produtos e importação de vendas, com autenticação via JWT e validação de dados com Pydantic.

Projeto desenvolvido durante o curso [**Flask: desenvolvendo APIs e aplicações web com MongoDB**](https://cursos.alura.com.br/course/python-web-flask) (Alura). O repositório é mantido tanto como vitrine quanto como **material de estudo** — por isso decisões que não seriam aceitáveis em produção estão preservadas e sinalizadas de propósito (o `.env` versionado é o exemplo mais evidente).

---

## 🏢 Sobre a empresa fictícia

---

**StyleSync** é uma rede fictícia de varejo de moda multimarca, com lojas físicas espalhadas por diferentes praças e um e-commerce próprio. Cada loja opera com relativa autonomia: mantém seu próprio estoque e, ao fim do expediente, exporta o movimento do dia em um arquivo CSV gerado pelo PDV local.

O nome do projeto vem justamente daí — *sync*. O catálogo é um só, mas vive fragmentado entre pontos de venda que não conversam entre si.

---

## 🎯 Problema de negócio

---

A StyleSync não tem uma fonte única de verdade para produto e venda. O catálogo é replicado manualmente entre lojas, o estoque diverge do que está anunciado, e o consolidado de vendas depende de alguém abrir planilha por planilha no fim do mês.

O que o sistema precisa resolver:

- **Catálogo centralizado** — um único cadastro de produtos (nome, preço, descrição, estoque) que qualquer canal consome.
- **Escrita controlada** — leitura do catálogo é pública, mas criar, alterar ou remover produto exige autenticação.
- **Ingestão de vendas em lote** — receber o CSV que cada loja já produz, sem obrigar o PDV a falar a língua da API.
- **Tolerância a linha suja** — um CSV com erro em algumas linhas não pode derrubar a importação inteira; o que é válido entra, o que não é volta reportado.

---

## 🚀 Tecnologias & conceitos aplicados

---

- **Flask** — construção da API, roteamento e serialização de respostas com `jsonify`
- **Application Factory** (`create_app()`) — instância da app criada sob demanda em vez de global no import
- **Blueprints** — rotas isoladas em módulo próprio e registradas na factory
- **MongoDB / PyMongo** — persistência em banco de documentos, conexão obtida a partir da própria URI (`get_default_database()`)
- **Pydantic v2** — validação e tipagem dos payloads, com `Field(alias='_id')`, `ConfigDict` e `Optional` para campos parciais
- **JWT (PyJWT)** — emissão de token na autenticação e validação nos endpoints protegidos, com expiração e tratamento de `ExpiredSignatureError` / `InvalidTokenError`
- **Decorators** — `@token_required` com `functools.wraps` para proteger rotas sem duplicar lógica de autenticação
- **python-dotenv** — variáveis sensíveis (URI e chave secreta) carregadas do `.env` via classe `Config`
- **Upload multipart + `csv.DictReader`** — leitura do arquivo em memória com `io.StringIO`, sem gravar em disco
- **`insert_many`** — inserção em lote das vendas válidas em uma única ida ao banco
- **Pytest** — testes unitários das funções de apoio
- **Separação de responsabilidades** — `models/` (formato dos dados), `routes/` (regra de entrada), `decorators.py` (autenticação), `config.py` (ambiente), `run.py` (entrypoint)

---

## 🧠 Decisões técnicas

---

- **Application Factory em vez de app global.** O `create_app()` centraliza configuração, conexão com o banco e registro de blueprints em um ponto só. O `run.py` fica sendo apenas o entrypoint, e a app passa a poder ser instanciada com configurações diferentes — o que é o que torna teste de rota possível mais adiante sem gambiarra.

- **Pydantic como fronteira da API, não como ORM.** O MongoDB é schemaless por natureza; a validação de formato acontece na borda, antes de qualquer escrita. Os modelos definem o contrato — o banco só guarda o que já passou por ele.

- **Modelo de leitura separado do modelo de escrita.** `Product` descreve o produto; `ProductDBModel` estende esse modelo sobrescrevendo `model_dump()` só para converter o `ObjectId` do Mongo em string serializável. A conversão fica em um lugar só, em vez de espalhada em cada rota que devolve produto.

- **`UpdateProduct` com todos os campos opcionais.** O `PUT` usa um modelo próprio em que nada é obrigatório, combinado com `exclude_unset=True` no `model_dump()`. Assim uma atualização parcial altera apenas os campos efetivamente enviados, em vez de sobrescrever o documento inteiro com `None` no que o cliente não mandou.

- **Autenticação por decorator, não por checagem dentro da rota.** O `@token_required` extrai e valida o token do header `Authorization`, e injeta o payload decodificado como primeiro argumento da função protegida. Cada rota decide se precisa de auth ou não pela presença do decorator — a lógica de validação existe uma vez só.

- **Leitura pública, escrita protegida.** `GET /products` e `GET /product/<id>` são abertos porque alimentam vitrine e canais de consulta. `POST`, `PUT`, `DELETE` e o upload de vendas exigem token.

- **Importação parcial em vez de tudo-ou-nada.** Na leitura do CSV, cada linha é validada isoladamente: as válidas entram no lote de inserção, as inválidas são acumuladas em uma lista de erros com o número da linha. A resposta devolve quantas vendas foram importadas **e** quais linhas falharam, em vez de rejeitar o arquivo inteiro por causa de um registro ruim.

- **Arquivo processado em memória.** O CSV chega como stream e é lido via `io.StringIO`, sem passar por disco — não há arquivo temporário para gerenciar nem limpar.

- **`.env` versionado de propósito.** Em qualquer projeto real esse arquivo estaria no `.gitignore`. Aqui ele está commitado deliberadamente, com as credenciais de desenvolvimento local, para que o repositório sirva como material de estudo completo e reproduzível. Os valores são locais e sem valor fora deste contexto.

---

## 🔐 Autenticação

---

O login valida credenciais **fixas de desenvolvimento** (`admin` / `123`, definidas no próprio código) e devolve um JWT assinado em `HS256` com validade de **30 minutos**. Não há cadastro nem persistência de usuário — o escopo do projeto é o fluxo de tokenização, não a gestão de identidade.

```bash
# 1. obter o token
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123"}'

# 2. usar o token nas rotas protegidas
curl -X POST http://localhost:5000/products \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Camisa Linho","price":189.90,"stock":24}'
```

---

## 📡 Endpoints

---

| Método | Rota | Auth | Descrição |
|---|---|:---:|---|
| `GET` | `/` | — | Healthcheck / mensagem de boas-vindas |
| `POST` | `/login` | — | Autentica e devolve o `access_token` (JWT, 30 min) |
| `GET` | `/products` | — | Lista todos os produtos do catálogo |
| `POST` | `/products` | 🔒 | Cria um novo produto |
| `GET` | `/product/<id>` | — | Detalha um produto pelo `ObjectId` |
| `PUT` | `/product/<id>` | 🔒 | Atualização parcial de um produto |
| `DELETE` | `/product/<id>` | 🔒 | Remove um produto (`204 No Content`) |
| `POST` | `/sales/upload` | 🔒 | Importa vendas em lote a partir de um CSV (`multipart/form-data`, campo `file`) |

---

## 🧾 Modelos de dados

---

**Produto** — coleção `products`

| Campo | Tipo | Obrigatório |
|---|---|:---:|
| `_id` | `ObjectId` | gerado pelo banco |
| `name` | `str` | ✅ |
| `price` | `float` | ✅ |
| `description` | `str` | — |
| `stock` | `int` | ✅ |

**Venda** — coleção `sale`

| Campo | Tipo | Obrigatório |
|---|---|:---:|
| `sale_date` | `date` | ✅ |
| `product_id` | `str` | ✅ |
| `quantify` | `int` | ✅ |
| `total_value` | `float` | ✅ |

O CSV de importação deve trazer exatamente esses nomes de coluna no cabeçalho:

```csv
sale_date,product_id,quantify,total_value
2026-08-14,68a1f3c4e2b5a90d1c7f4e21,2,379.80
2026-08-14,68a1f3c4e2b5a90d1c7f4e22,1,129.90
```

---

## ⚠️ Maiores desafios

---

- Entender o ciclo de vida da application factory — em que ponto a conexão com o banco existe e a partir de quando os módulos de rota podem consumi-la
- Fazer o `ObjectId` do MongoDB atravessar o Pydantic e chegar ao JSON de resposta (`arbitrary_types_allowed`, alias `_id`, sobrescrita do `model_dump()`)
- Diferenciar atualização parcial de substituição total, e descobrir que isso exige um modelo próprio para o `PUT` em vez de reaproveitar o modelo de criação
- Escrever um decorator que preserva a assinatura e os metadados da função original e ainda repassa o payload do token para rotas com parâmetros de rota diferentes entre si
- Encaixar a ordem dos decorators (`@route` acima de `@token_required`) e entender por que a inversão quebra o registro da rota
- Tratar o arquivo enviado como stream em memória em vez de arquivo em disco
- Validar linha a linha no CSV mantendo a importação parcial, sem deixar uma exceção interromper o laço
- Separar o que é erro de validação (`ValidationError`, culpa do cliente) do que é erro inesperado, devolvendo respostas diferentes para cada caso
- Manter as variáveis sensíveis fora do código e disponíveis para `current_app.config` dentro do contexto de requisição

---

## 🗂️ Estrutura do projeto

---

```
Stylesync/
├── stylesync_flask/            # projeto principal — API REST Flask + MongoDB
│   ├── app/
│   │   ├── __init__.py         # application factory e conexão com o MongoDB
│   │   ├── decorators.py       # @token_required — validação do JWT
│   │   ├── utils.py            # funções de apoio (formatação)
│   │   ├── models/             # schemas Pydantic
│   │   │   ├── products.py     # Product, ProductDBModel, UpdateProduct
│   │   │   ├── sale.py         # Sale
│   │   │   └── user.py         # LoginPayload
│   │   └── routes/
│   │       └── main.py         # blueprint principal com todos os endpoints
│   ├── tests/
│   │   └── test_utils.py       # testes unitários (pytest)
│   ├── config.py               # leitura das variáveis de ambiente
│   ├── run.py                  # entrypoint da aplicação
│   ├── requirements.txt        # dependências do projeto
│   └── .env                    # variáveis de ambiente (versionado de propósito)
└── structure_tests/            # estudos comparativos de estrutura
    ├── native/                 # servidor WSGI puro (PEP 3333), sem framework
    │   ├── aplicacao_web.py    # servidor + aplicação escritos na mão
    │   └── index.html          # template com placeholder {{PRODUTOS}}
    ├── stylesync_django/       # esqueleto Django (projeto + app `core`)
    └── stylesync_FastAPI/      # esqueleto FastAPI
```

---

## 🔬 Sobre a pasta `structure_tests`

---

Antes de definir a stack da API, montei o mesmo "olá mundo" em quatro abordagens diferentes para comparar como cada uma organiza responsabilidades:

- **`native/`** — servidor WSGI escrito na mão com `wsgiref.simple_server`, seguindo a PEP 3333. Serve para enxergar o que um framework faz por baixo: montar o status e os headers da resposta na mão via `start_response`, ler o `index.html` do disco e substituir o placeholder `{{PRODUTOS}}` por HTML gerado em laço — ou seja, roteamento, template engine e serialização feitos manualmente.
- **`stylesync_django/`** — esqueleto Django, com a divisão projeto/app (`projeto_django` + `core`), `urls.py` encadeado por `include()`, ORM e admin já acoplados e SQLite como banco padrão. O contraste com o Flask fica claro no volume de decisão que já vem tomada.
- **`stylesync_FastAPI/`** — esqueleto FastAPI, com tipagem e documentação automática a partir das assinaturas.

Não são projetos paralelos em andamento: são referência de estudo que justifica a escolha do Flask para o StyleSync — framework enxuto o suficiente para que a arquitetura fosse decisão minha, e não do scaffold.

---

## ▶️ Como executar

---

**Pré-requisitos:** Python 3.14 e uma instância do MongoDB rodando localmente na porta padrão (`27017`).

```bash
git clone https://github.com/oJuanMarco/Stylesync
cd Stylesync/stylesync_flask
pip install -r requirements.txt
python run.py
```

A API sobe em `http://localhost:5000` em modo debug. O banco `stylesync` é criado automaticamente pelo MongoDB na primeira escrita — o catálogo começa vazio, então o primeiro passo é autenticar e cadastrar produtos via `POST /products`.

Variáveis esperadas no `.env`:

```
MONGO_URI=mongodb://localhost:27017/stylesync
SECRET_KEY=UmaSenhaSecreta
```

---

## 🧪 Testes

---

```bash
cd stylesync_flask
pytest
```

---

## 👤 Autor

---

**Juan Marco**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Conectar-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/ojuanmarco/)
[![GitHub](https://img.shields.io/badge/GitHub-Perfil-181717?style=flat&logo=github)](https://github.com/oJuanMarco)

---
---

# 👗 StyleSync

REST API in Python (Flask) with MongoDB persistence for product catalog management and sales import, featuring JWT authentication and Pydantic data validation.

Built during the Alura course [**Flask: desenvolvendo APIs e aplicações web com MongoDB**](https://cursos.alura.com.br/course/python-web-flask). This repository is kept both as a showcase and as **study material** — which is why decisions that would never ship to production are deliberately preserved and flagged (the committed `.env` being the most visible one).

---

## 🏢 About the fictional company

---

**StyleSync** is a fictional multi-brand fashion retail chain, with physical stores across different regions and its own e-commerce channel. Each store operates with relative autonomy: it keeps its own stock and, at closing time, exports the day's movement as a CSV file generated by the local POS system.

That's where the project name comes from — *sync*. There is a single catalog, but it lives fragmented across points of sale that don't talk to each other.

---

## 🎯 Business problem

---

StyleSync has no single source of truth for products and sales. The catalog is replicated by hand across stores, stock diverges from what's advertised, and the consolidated sales figure depends on someone opening spreadsheet after spreadsheet at month's end.

What the system needs to solve:

- **Centralized catalog** — one product registry (name, price, description, stock) consumed by every channel.
- **Controlled writes** — reading the catalog is public, but creating, updating or deleting a product requires authentication.
- **Batch sales ingestion** — accept the CSV each store already produces, without forcing the POS to speak the API's language.
- **Tolerance for dirty rows** — a CSV with a few bad lines can't bring down the whole import; valid records go in, invalid ones come back reported.

---

## 🚀 Technologies & concepts applied

---

- **Flask** — API construction, routing and response serialization with `jsonify`
- **Application Factory** (`create_app()`) — app instance created on demand instead of as an import-time global
- **Blueprints** — routes isolated in their own module and registered by the factory
- **MongoDB / PyMongo** — document-store persistence, with the database resolved from the connection URI itself (`get_default_database()`)
- **Pydantic v2** — payload validation and typing, using `Field(alias='_id')`, `ConfigDict` and `Optional` for partial payloads
- **JWT (PyJWT)** — token issuing on login and validation on protected endpoints, with expiration and handling of `ExpiredSignatureError` / `InvalidTokenError`
- **Decorators** — `@token_required` with `functools.wraps` to protect routes without duplicating auth logic
- **python-dotenv** — sensitive variables (URI and secret key) loaded from `.env` through a `Config` class
- **Multipart upload + `csv.DictReader`** — file read in memory via `io.StringIO`, never touching disk
- **`insert_many`** — valid sales inserted as a single batch round-trip
- **Pytest** — unit tests for helper functions
- **Separation of concerns** — `models/` (data shape), `routes/` (entry rules), `decorators.py` (auth), `config.py` (environment), `run.py` (entrypoint)

---

## 🧠 Technical decisions

---

- **Application factory over a global app.** `create_app()` centralizes configuration, database connection and blueprint registration in one place. `run.py` is reduced to an entrypoint, and the app becomes instantiable with different configurations — which is what makes route testing possible later without hacks.

- **Pydantic as the API boundary, not as an ORM.** MongoDB is schemaless by nature; format validation happens at the edge, before any write. The models define the contract — the database only stores what already passed through it.

- **Read model separated from write model.** `Product` describes a product; `ProductDBModel` extends it, overriding `model_dump()` solely to turn Mongo's `ObjectId` into a serializable string. The conversion lives in one place instead of being scattered across every route that returns a product.

- **`UpdateProduct` with every field optional.** `PUT` uses a dedicated model where nothing is required, combined with `exclude_unset=True` on `model_dump()`. A partial update then touches only the fields actually sent, instead of overwriting the whole document with `None` wherever the client stayed silent.

- **Auth via decorator, not via checks inside the route.** `@token_required` extracts and validates the token from the `Authorization` header and injects the decoded payload as the protected function's first argument. Each route declares its auth requirement by the decorator's presence — the validation logic exists exactly once.

- **Public reads, protected writes.** `GET /products` and `GET /product/<id>` are open because they feed storefront and lookup channels. `POST`, `PUT`, `DELETE` and the sales upload require a token.

- **Partial import over all-or-nothing.** While reading the CSV, each row is validated in isolation: valid ones join the insertion batch, invalid ones are accumulated in an error list with their line number. The response returns how many sales were imported **and** which lines failed, instead of rejecting the entire file over one bad record.

- **File processed in memory.** The CSV arrives as a stream and is read through `io.StringIO`, never hitting disk — no temporary file to manage or clean up.

- **`.env` committed on purpose.** In any real project this file would sit in `.gitignore`. Here it is deliberately versioned, holding local development credentials, so the repository works as complete, reproducible study material. The values are local and worthless outside this context.

---

## 🔐 Authentication

---

Login validates **fixed development credentials** (`admin` / `123`, defined in the code itself) and returns a JWT signed with `HS256`, valid for **30 minutes**. There is no user registration or persistence — the project's scope is the tokenization flow, not identity management.

```bash
# 1. get the token
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123"}'

# 2. use the token on protected routes
curl -X POST http://localhost:5000/products \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Linen Shirt","price":189.90,"stock":24}'
```

---

## 📡 Endpoints

---

| Method | Route | Auth | Description |
|---|---|:---:|---|
| `GET` | `/` | — | Healthcheck / welcome message |
| `POST` | `/login` | — | Authenticates and returns the `access_token` (JWT, 30 min) |
| `GET` | `/products` | — | Lists every product in the catalog |
| `POST` | `/products` | 🔒 | Creates a new product |
| `GET` | `/product/<id>` | — | Retrieves a single product by `ObjectId` |
| `PUT` | `/product/<id>` | 🔒 | Partial update of a product |
| `DELETE` | `/product/<id>` | 🔒 | Deletes a product (`204 No Content`) |
| `POST` | `/sales/upload` | 🔒 | Batch-imports sales from a CSV (`multipart/form-data`, field `file`) |

---

## 🧾 Data models

---

**Product** — collection `products`

| Field | Type | Required |
|---|---|:---:|
| `_id` | `ObjectId` | generated by the database |
| `name` | `str` | ✅ |
| `price` | `float` | ✅ |
| `description` | `str` | — |
| `stock` | `int` | ✅ |

**Sale** — collection `sale`

| Field | Type | Required |
|---|---|:---:|
| `sale_date` | `date` | ✅ |
| `product_id` | `str` | ✅ |
| `quantify` | `int` | ✅ |
| `total_value` | `float` | ✅ |

The import CSV must carry exactly these column names in its header:

```csv
sale_date,product_id,quantify,total_value
2026-08-14,68a1f3c4e2b5a90d1c7f4e21,2,379.80
2026-08-14,68a1f3c4e2b5a90d1c7f4e22,1,129.90
```

---

## ⚠️ Main challenges

---

- Understanding the application factory lifecycle — at which point the database connection exists and from when route modules may consume it
- Getting MongoDB's `ObjectId` through Pydantic and into the JSON response (`arbitrary_types_allowed`, the `_id` alias, overriding `model_dump()`)
- Telling partial update apart from full replacement, and discovering that it requires a dedicated model for `PUT` rather than reusing the creation model
- Writing a decorator that preserves the original function's signature and metadata while still forwarding the token payload to routes with differing path parameters
- Getting decorator order right (`@route` above `@token_required`) and understanding why inverting it breaks route registration
- Handling the uploaded file as an in-memory stream rather than a file on disk
- Validating the CSV row by row while keeping the import partial, without letting one exception break the loop
- Separating validation errors (`ValidationError`, the client's fault) from unexpected errors, returning different responses for each
- Keeping sensitive variables out of the code while still available to `current_app.config` inside the request context

---

## 🗂️ Project structure

---

```
Stylesync/
├── stylesync_flask/            # main project — Flask + MongoDB REST API
│   ├── app/
│   │   ├── __init__.py         # application factory and MongoDB connection
│   │   ├── decorators.py       # @token_required — JWT validation
│   │   ├── utils.py            # helper functions (formatting)
│   │   ├── models/             # Pydantic schemas
│   │   │   ├── products.py     # Product, ProductDBModel, UpdateProduct
│   │   │   ├── sale.py         # Sale
│   │   │   └── user.py         # LoginPayload
│   │   └── routes/
│   │       └── main.py         # main blueprint with every endpoint
│   ├── tests/
│   │   └── test_utils.py       # unit tests (pytest)
│   ├── config.py               # environment variable loading
│   ├── run.py                  # application entrypoint
│   ├── requirements.txt        # project dependencies
│   └── .env                    # environment variables (committed on purpose)
└── structure_tests/            # comparative structure studies
    ├── native/                 # raw WSGI server (PEP 3333), no framework
    │   ├── aplicacao_web.py    # server + application written by hand
    │   └── index.html          # template with a {{PRODUTOS}} placeholder
    ├── stylesync_django/       # Django skeleton (project + `core` app)
    └── stylesync_FastAPI/      # FastAPI skeleton
```

---

## 🔬 About the `structure_tests` folder

---

Before settling on the API's stack, I built the same "hello world" in four different approaches to compare how each one organizes responsibilities:

- **`native/`** — a WSGI server written by hand with `wsgiref.simple_server`, following PEP 3333. Useful for seeing what a framework does underneath: assembling status and headers manually through `start_response`, reading `index.html` from disk and replacing the `{{PRODUTOS}}` placeholder with HTML built in a loop — routing, template engine and serialization all done by hand.
- **`stylesync_django/`** — Django skeleton, with its project/app split (`projeto_django` + `core`), `urls.py` chained through `include()`, ORM and admin already bolted on, and SQLite as the default database. The contrast with Flask shows up in how many decisions arrive already made.
- **`stylesync_FastAPI/`** — FastAPI skeleton, with typing and automatic documentation derived from function signatures.

These aren't parallel projects in progress: they're study references that justify choosing Flask for StyleSync — a framework lean enough that the architecture was my decision, not the scaffold's.

---

## ▶️ How to run

---

**Prerequisites:** Python 3.14 and a MongoDB instance running locally on the default port (`27017`).

```bash
git clone https://github.com/oJuanMarco/Stylesync
cd Stylesync/stylesync_flask
pip install -r requirements.txt
python run.py
```

The API starts at `http://localhost:5000` in debug mode. The `stylesync` database is created automatically by MongoDB on the first write — the catalog starts empty, so the first step is to authenticate and register products via `POST /products`.

Expected variables in `.env`:

```
MONGO_URI=mongodb://localhost:27017/stylesync
SECRET_KEY=UmaSenhaSecreta
```

---

## 🧪 Tests

---

```bash
cd stylesync_flask
pytest
```

---

## 👤 Author

---

**Juan Marco**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Conectar-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/ojuanmarco/)
[![GitHub](https://img.shields.io/badge/GitHub-Perfil-181717?style=flat&logo=github)](https://github.com/oJuanMarco)
