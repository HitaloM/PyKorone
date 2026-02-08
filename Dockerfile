FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_DEV=1 UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

FROM python:3.14-slim-trixie AS runtime

RUN groupadd --system --gid 999 nonroot \
 && useradd --system --uid 999 --gid 999 --create-home nonroot

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends whois \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder --chown=nonroot:nonroot /app/.venv /app/.venv
COPY --from=builder --chown=nonroot:nonroot /app/locales /app/locales
COPY --from=builder --chown=nonroot:nonroot /app/data /app/data

ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

USER nonroot

WORKDIR /app

CMD ["python", "-m", "korone"]
