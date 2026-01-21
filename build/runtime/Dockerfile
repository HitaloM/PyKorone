FROM python:3.13-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc git pkg-config libicu-dev && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /build

COPY pyproject.toml uv.lock ./
COPY libs libs

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-editable
COPY sophie_bot sophie_bot
COPY locales locales
COPY Makefile Makefile

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable

RUN uv run --no-sync python -c "from babel.messages import frontend; import sys; sys.exit(frontend.compile_catalog.main(argv=['--directory', 'locales', '--domain', 'sophie']))"

RUN uv build --wheel

ARG BRANCH_NAME=Local
ARG COMMIT_HASH=unknown
RUN echo "SOPHIE_COMMIT = \"$COMMIT_HASH\"" > /build/sophie_bot/versions.py && \
    echo "SOPHIE_BRANCH = \"$BRANCH_NAME\"" >> /build/sophie_bot/versions.py

RUN uv pip install --system dist/*.whl --no-deps

FROM python:3.13-slim

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends libicu-dev && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python*/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /build/sophie_bot /sophie_bot
COPY --from=builder /build/locales /locales
COPY --from=builder /build/migrations /migrations

WORKDIR /

ENTRYPOINT ["python", "-m", "sophie_bot"]
CMD ["bot"]
