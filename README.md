# Resale Market API

Reservation and purchase API for a resale marketplace. Every product exists in a single copy
and moves through `AVAILABLE → RESERVED → SOLD`.

**Key guarantee:** when several users order the same product at the same time, exactly one of
them gets it.

**Stack:** Python 3.12, FastAPI, PostgreSQL 17, SQLAlchemy 2.0 (async, asyncpg), Alembic,
Pydantic v2, uv, Ruff, pytest, Docker Compose, GitHub Actions.

## Quick start

```bash
make up        # same as docker compose up --build
```

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI schema: http://localhost:8000/openapi.json

Migrations run automatically when the container starts. If ports `8000` or `5432` are taken,
pick others: `API_PORT=8080 POSTGRES_PORT=5433 make up`.

Run `make` to list all commands, see also [Coming from Rails](#coming-from-rails).

## Demo frontend

React + shadcn/ui client: [market_react](https://github.com/andreiyurik/market_react).
It shows the catalog, ordering, payment and a "20 buyers at once" button that demonstrates
the race condition protection. The whole stack (database, API, frontend and demo data) starts
with one command from that repository: `docker compose up --build`, then open
http://localhost:5173.

## API

| Method | Path               | Description                                     | Responses          |
|--------|--------------------|-------------------------------------------------|--------------------|
| POST   | `/products`        | Create a product (status `AVAILABLE`)           | 201, 422           |
| GET    | `/products`        | List products, newest first (`limit`, `offset`) | 200, 422           |
| GET    | `/products/{id}`   | Get a product                                   | 200, 404, 422      |
| POST   | `/orders`          | Create an order and reserve the product         | 201, 404, 409, 422 |
| POST   | `/orders/{id}/pay` | Pay for an order: the product becomes `SOLD`    | 200, 404, 409, 422 |
| GET    | `/health`          | Health check                                    | 200                |

`409 Conflict` means the product is already reserved or sold, or the order is already paid.
All errors share one format: `{"detail": "..."}`.

```bash
curl -X POST localhost:8000/products -H 'Content-Type: application/json' \
  -d '{"title": "Leica M6", "price": "2500.00"}'

curl -X POST localhost:8000/orders -H 'Content-Type: application/json' \
  -d '{"product_id": "<product id>"}'
```

Prices are sent as strings (`"2500.00"`): they are `Decimal`, so no float rounding errors.

## Frontend integration

1. **Docs and manual testing:** Swagger UI at http://localhost:8000/docs, where any endpoint
   can be called with "Try it out".
2. **API contract:** [`openapi.json`](openapi.json) is committed, so clients can be generated
   without running the backend, and every API change shows up in the PR diff. The
   `test_committed_openapi_schema_is_up_to_date` test keeps it in sync. After changing the API:

   ```bash
   make openapi
   ```

3. **Typed TypeScript client:** every endpoint has a stable `operationId`
   (`products-create_product`, `orders-pay_order`), so generated functions get clean names:

   ```bash
   npm i -D @hey-api/openapi-ts typescript@5
   npx openapi-ts -i ../market_fastapi/openapi.json -o src/client
   # or from a running server: -i http://localhost:8000/openapi.json
   ```

   This produces functions like `productsCreateProduct` and `ordersPayOrder`, and types like
   `ProductStatus = 'AVAILABLE' | 'RESERVED' | 'SOLD'`. The generator needs TypeScript 5 or 6;
   it does not work with TypeScript 7 yet.

4. **CORS:** allowed origins are set in `BACKEND_CORS_ORIGINS`. In Docker the defaults are
   `http://localhost:5173` (Vite) and `http://localhost:3000` (Next.js).

## Architecture

The app has three layers, and dependencies only point down:

```
api/routes    HTTP: request validation, status codes, OpenAPI  →  services
services      business rules and transactions, no HTTP         →  repositories
repositories  SQL queries via SQLAlchemy                       →  PostgreSQL
```

- **Routes** take a Pydantic schema, call a service and return a response schema.
- **Services** enforce the rules (e.g. "only an `AVAILABLE` product can be ordered"), own the
  transaction (`commit`) and raise domain exceptions (`ProductNotFoundError`,
  `ProductNotAvailableError`).
- **Repositories** only run database queries, with no business rules.
- Domain exceptions are mapped to HTTP responses in one place, `app/api/errors.py`
  (`NotFoundError → 404`, `ConflictError → 409`).
- The DB session and services are provided through FastAPI dependency injection
  (`app/api/deps.py`), so layers are easy to swap in tests.

```
app/
├── main.py              # FastAPI app, CORS, OpenAPI
├── core/
│   ├── config.py        # settings from environment variables (pydantic-settings)
│   └── db.py            # async engine and session
├── models.py            # ORM models Product, Order
├── schemas.py           # Pydantic request and response schemas
├── repositories/        # database access layer
├── services/            # business logic and domain exceptions
└── api/
    ├── deps.py          # dependencies (session, services)
    ├── errors.py        # domain exceptions → HTTP
    ├── main.py          # router assembly
    └── routes/          # products.py, orders.py
alembic/                 # database migrations
tests/                   # integration tests against real PostgreSQL
scripts/                 # OpenAPI export, demo seed, DB init SQL
openapi.json             # API contract for frontends
```

## Concurrency

A reservation is a single atomic conditional `UPDATE` (`ProductRepository.change_status`):

```sql
UPDATE products SET status = 'RESERVED'
WHERE id = :id AND status = 'AVAILABLE'
RETURNING *;
```

When several transactions update the same row, PostgreSQL locks it for the first one. The
others wait, and after the first commits they **re-check** the `WHERE` condition, see
`RESERVED` and update nothing. If the `UPDATE` returned a row, the order is created in the same
transaction. If not, the service returns `404` (no such product) or `409` (already taken).

Why this approach:
- **One statement instead of read → check → write.** With the naive version both requests read
  `AVAILABLE` and both create an order.
- **The database gives the guarantee**, so it holds for any number of workers, processes and
  instances. An in-process lock (`asyncio.Lock`) only protects a single process.
- **No extra infrastructure** such as a distributed lock in Redis.

Payment (`POST /orders/{id}/pay`) uses the same mechanism for `RESERVED → SOLD`, so an order
cannot be paid twice, even by concurrent requests.

The alternative is pessimistic locking: `SELECT ... FOR UPDATE`, check the status, then
`UPDATE`. It is also correct, but takes two statements and holds the row lock longer. Another
option is optimistic locking with a `version` column.

`tests/test_concurrency.py` sends 20 concurrent orders for one product and checks that exactly
one gets `201`, the rest get `409`, and the database holds exactly one order. The naive
implementation fails this test.

## Local development

Requires [uv](https://docs.astral.sh/uv/) (Python package manager), Docker and `make`.

```bash
make setup     # dependencies + .env from .env.example
make db        # PostgreSQL in Docker
make migrate   # apply migrations
make seed      # demo products (wipes current data)
make dev       # dev server with auto-reload at http://localhost:8000
```

Tests use a separate `app_test` database (created on the first start of the PostgreSQL
container) and never touch development data:

```bash
make test      # tests + coverage report (95% threshold)
make lint      # code style checks
```

CI (GitHub Actions) runs on every push and pull request: linting, a check that migrations apply
and match the models (`alembic check`), tests against PostgreSQL with coverage, and a Docker
image build.

## Coming from Rails

Short commands live in the [`Makefile`](Makefile). They wrap plain `uv run …` calls, which can
also be run directly.

| Task                  | Rails                            | Here                           |
|-----------------------|----------------------------------|--------------------------------|
| List commands         | `bin/rails --help`               | `make`                         |
| Install dependencies  | `bundle install`                 | `make setup`                   |
| Add a library         | `bundle add <gem>`               | `uv add <package>`             |
| Run the server        | `bin/rails server`               | `make dev`                     |
| Run everything        | `docker compose up`              | `make up`                      |
| Apply migrations      | `bin/rails db:migrate`           | `make migrate`                 |
| Create a migration    | `bin/rails g migration AddField` | `make migration m="add field"` |
| Load demo data        | `bin/rails db:seed:replant`      | `make seed`                    |
| Roll back a migration | `bin/rails db:rollback`          | `make rollback`                |
| Run tests             | `bin/rails test`                 | `make test`                    |
| Check code style      | `bin/rubocop`                    | `make lint`                    |
| Fix code style        | `bin/rubocop -a`                 | `make format`                  |
| Show routes           | `bin/rails routes`               | Swagger: `/docs`               |

Where things live:

| Rails                                    | Here                         | What it is                           |
|------------------------------------------|------------------------------|--------------------------------------|
| `Gemfile`                                | `pyproject.toml`             | dependencies, edited by hand         |
| `Gemfile.lock`                           | `uv.lock`                    | pinned versions, generated           |
| `config/database.yml`, credentials       | `.env`, `app/core/config.py` | settings                             |
| `config/routes.rb` + controllers         | `app/api/routes/`            | HTTP layer                           |
| strong parameters, serializers           | `app/schemas.py`             | input validation and response format |
| `app/models/` (ActiveRecord)             | `app/models.py`              | tables                               |
| scopes and queries in models             | `app/repositories/`          | database queries                     |
| service objects (`app/services/`)        | `app/services/`              | business logic                       |
| `rescue_from` in `ApplicationController` | `app/api/errors.py`          | errors → HTTP status codes           |
| `db/migrate/`                            | `alembic/versions/`          | migrations                           |
| `test/`, `spec/`                         | `tests/`                     | tests                                |

The main difference from Rails: SQLAlchemy is not ActiveRecord. A model only describes a
table, and queries live in repositories, so layers that Rails often mixes inside the model are
kept separate here.

## Roadmap

- **Reservation expiry:** an `expires_at` on orders, and a background job that returns unpaid
  products to `AVAILABLE`.
- **Users and auth:** JWT, `user_id` on orders.
- **Kafka:** an `OrderCreated` event for other services (notifications, analytics) via a
  transactional outbox, so events are never lost or sent without a commit.
- **Redis:** rate limiting for order creation, caching for `GET /products/{id}`.
- **OpenSearch:** full-text catalog search.
- **Nginx:** reverse proxy, TLS, a single entry point for web and mobile. API versioning
  (`/api/v1`).
- **Migrations:** a separate deploy step in production instead of running in every container.

## Conventions

- Commits follow [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat:`, `fix:`, `test:`, `build:`, `ci:`, `docs:`, `chore:`).
- Linear history: branches are updated with rebase, PRs are merged with rebase merge.
