FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

FROM python:3.14-slim-trixie AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system --gid 999 korone && \
    useradd --system --uid 999 --gid 999 --create-home korone

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends whois && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder --chown=korone:korone /app/.venv /app/.venv
COPY --from=builder --chown=korone:korone /app/alembic.ini /app/alembic.ini
COPY --from=builder --chown=korone:korone /app/alembic /app/alembic
COPY --from=builder --chown=korone:korone /app/locales /app/locales
COPY --from=builder --chown=korone:korone /app/src/korone /app/src/korone
COPY --from=builder --chown=korone:korone /app/data /app/data

USER korone

ENTRYPOINT ["python"]
CMD ["-m", "korone"]
