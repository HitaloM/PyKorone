FROM python:3.14-rc-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1

ENV UV_LINK_MODE=copy

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libjpeg62-turbo-dev \
        libpq-dev \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

FROM python:3.14-rc-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY --from=builder /app/locales /app/locales
COPY --from=builder /app/data /app/data

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "korone"]
