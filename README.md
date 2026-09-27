# Resale Market API

API резервирования и покупки товаров для ресейл-маркетплейса. Каждый товар существует
в одном экземпляре и проходит статусы `AVAILABLE → RESERVED → SOLD`.

**Главное требование:** если два пользователя одновременно создают заказ на один товар,
зарезервировать его успешно должен только один.

**Стек:** Python 3.12, FastAPI, PostgreSQL 17, SQLAlchemy 2.0 (async, asyncpg), Alembic,
Pydantic v2, uv, Ruff, pytest, Docker Compose, GitHub Actions.

## Быстрый старт

```bash
docker compose up --build
```

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI-схема: http://localhost:8000/openapi.json

Миграции применяются автоматически при старте контейнера. Если порты `8000` или `5432`
заняты, задайте другие: `API_PORT=8080 POSTGRES_PORT=5433 docker compose up --build`.

## API

| Метод | Путь               | Описание                                | Ответы             |
|-------|--------------------|-----------------------------------------|--------------------|
| POST  | `/products`        | Создать товар (статус `AVAILABLE`)      | 201, 422           |
| GET   | `/products/{id}`   | Получить товар                          | 200, 404, 422      |
| POST  | `/orders`          | Создать заказ и зарезервировать товар   | 201, 404, 409, 422 |
| POST  | `/orders/{id}/pay` | Оплатить заказ: товар становится `SOLD` | 200, 404, 409, 422 |
| GET   | `/health`          | Проверка работоспособности              | 200                |

`409 Conflict` означает, что товар уже зарезервирован или продан (или заказ уже оплачен). Ошибки имеют единый формат
`{"detail": "..."}`.

```bash
curl -X POST localhost:8000/products -H 'Content-Type: application/json' \
  -d '{"title": "Leica M6", "price": "2500.00"}'

curl -X POST localhost:8000/orders -H 'Content-Type: application/json' \
  -d '{"product_id": "<id товара>"}'
```

Цена передаётся строкой (`"2500.00"`): это `Decimal`, чтобы не терять точность, как с `float`.

## Интеграция с фронтендом (React)

Разрешённые origin'ы для CORS задаются в `BACKEND_CORS_ORIGINS`. По умолчанию в Docker это
`http://localhost:5173` (Vite) и `http://localhost:3000` (Next.js).

У каждого эндпоинта стабильный `operationId` (`products-create_product`,
`orders-create_order`), поэтому типизированный TypeScript-клиент генерируется из схемы:

```bash
npx @hey-api/openapi-ts -i http://localhost:8000/openapi.json -o src/client
```

## Архитектура

Приложение разделено на три слоя. Зависимости направлены только вниз:

```
api/routes    HTTP: валидация запроса, коды ответов, OpenAPI    →  services
services      бизнес-логика и транзакции, ничего не знает об HTTP →  repositories
repositories  SQL-запросы через SQLAlchemy                        →  PostgreSQL
```

- **Routes** принимают Pydantic-схему, вызывают сервис и возвращают схему ответа.
- **Services** реализуют правила (например, «заказать можно только `AVAILABLE`-товар»),
  управляют транзакцией (`commit`) и бросают доменные исключения (`ProductNotFoundError`,
  `ProductNotAvailableError`).
- **Repositories** содержат только запросы к БД, без бизнес-правил.
- Доменные исключения превращаются в HTTP-ответы в одном месте, в `app/api/errors.py`
  (`NotFoundError → 404`, `ConflictError → 409`).
- Сессия БД и сервисы передаются через FastAPI Dependency Injection (`app/api/deps.py`),
  поэтому слои легко подменить в тестах.

```
app/
├── main.py              # создание FastAPI-приложения, CORS, OpenAPI
├── core/
│   ├── config.py        # настройки из переменных окружения (pydantic-settings)
│   └── db.py            # async engine и сессия
├── models.py            # ORM-модели Product, Order
├── schemas.py           # Pydantic-схемы запросов и ответов
├── repositories/        # слой работы с БД
├── services/            # бизнес-логика и доменные исключения
└── api/
    ├── deps.py          # зависимости (сессия, сервисы)
    ├── errors.py        # доменные исключения → HTTP
    ├── main.py          # сборка роутеров
    └── routes/          # products.py, orders.py
alembic/                 # миграции БД
tests/                   # интеграционные тесты на реальном PostgreSQL
```

## Как решена конкурентность

Резервирование — один атомарный условный `UPDATE`
(`ProductRepository.change_status`):

```sql
UPDATE products SET status = 'RESERVED'
WHERE id = :id AND status = 'AVAILABLE'
RETURNING *;
```

Когда несколько транзакций одновременно обновляют одну строку, PostgreSQL блокирует её для
первой. Остальные ждут, после коммита первой **заново проверяют** условие `WHERE`, видят
`RESERVED` и ничего не обновляют. Если `UPDATE` вернул строку, в той же транзакции создаётся
заказ. Если не вернул, сервис отдаёт `404` (товара нет) или `409` (уже занят).

Почему так:
- **Одна операция вместо «прочитать → проверить → записать».** В наивном варианте оба запроса
  успевают прочитать `AVAILABLE`, и оба создают заказ.
- **Гарантию даёт база данных**, поэтому решение работает при любом количестве воркеров,
  процессов и инстансов. Блокировки в Python (`asyncio.Lock`) защищают только один процесс.
- **Не нужен дополнительный инфраструктурный компонент** вроде распределённого lock в Redis.

Оплата (`POST /orders/{id}/pay`) использует тот же механизм: `RESERVED → SOLD`, поэтому
заказ нельзя оплатить дважды даже при одновременных запросах.

Альтернатива — пессимистичная блокировка `SELECT ... FOR UPDATE`, затем проверка статуса и
`UPDATE`. Она тоже корректна, но требует двух запросов, а строка удерживается под блокировкой
дольше. Ещё один вариант — оптимистичная блокировка через колонку `version`.

Тест `tests/test_concurrency.py` отправляет 20 одновременных заказов на один товар и
проверяет, что ответов `201` ровно один, а остальные `409`, и что в БД ровно один заказ.
Наивная реализация на этом тесте падает.

## Локальная разработка

Нужен [uv](https://docs.astral.sh/uv/).

```bash
uv sync                                  # зависимости
cp .env.example .env                     # настройки
docker compose up -d db                  # только PostgreSQL
uv run alembic upgrade head              # миграции
uv run fastapi dev app/main.py           # сервер с автоперезагрузкой
```

Тесты используют отдельную базу `app_test` (она создаётся при первом запуске контейнера
PostgreSQL) и не трогают данные разработки:

```bash
uv run pytest --cov                      # тесты + отчёт о покрытии (порог 95%)
uv run ruff check . && uv run ruff format --check .
```

Новая миграция после изменения моделей:

```bash
uv run alembic revision --autogenerate -m "describe change"
```

CI (GitHub Actions) на каждый push и pull request запускает линтер, проверяет, что миграции
применяются и соответствуют моделям (`alembic check`), прогоняет тесты на PostgreSQL с
проверкой покрытия и собирает Docker-образ.

## Что дальше

Задание намеренно реализовано минимально. Как оно развивается в продакшн-систему:

- **Истечение резерва:** у заказа `expires_at`; фоновая задача возвращает неоплаченные товары
  в `AVAILABLE`.
- **Пользователи и авторизация:** JWT, `user_id` у заказа.
- **Kafka:** событие `OrderCreated` для других сервисов (уведомления, аналитика) через
  transactional outbox, чтобы событие не потерялось и не ушло без коммита.
- **Redis:** rate limiting на создание заказов, кеш для `GET /products/{id}`.
- **OpenSearch:** полнотекстовый поиск по каталогу.
- **Nginx:** reverse proxy, TLS, единая точка входа для web и mobile. Версионирование API
  (`/api/v1`).
- **Миграции:** в продакшене — отдельный шаг деплоя, а не запуск в каждом контейнере.

## Соглашения

- Коммиты по [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat:`, `fix:`, `test:`, `build:`, `ci:`, `docs:`, `chore:`).
- Линейная история: ветки обновляются через rebase, PR вливаются через rebase merge.
