FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# Install dependencies first: this layer is cached until uv.lock changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
# Maintenance scripts, e.g. `python -m scripts.seed` for demo data.
COPY scripts ./scripts
RUN uv sync --frozen --no-dev

# Run the app as an unprivileged user.
RUN useradd --system --no-create-home app
USER app

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && exec fastapi run app/main.py --port 8000"]
