FROM python:3.13-slim as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt update && \
    apt install -y --no-install-recommends build-essential gcc git pkg-config libicu-dev && \
    rm -rf /var/lib/apt/lists/*
RUN pip install uv
RUN python -m venv /venv

WORKDIR /build
COPY pyproject.toml uv.lock ./
COPY libs libs

RUN --mount=type=cache,target=/root/.cache/uv \
    uv export --no-hashes --no-editable --format requirements.txt | /venv/bin/pip install -r /dev/stdin

COPY sophie_bot sophie_bot
COPY locales locales
COPY Makefile Makefile

# Install dependencies and setup locale
RUN . /venv/bin/activate && \
    pip install Babel && \
    make compile_lang

RUN --mount=type=cache,target=/root/.cache/uv \
    uv build --wheel && /venv/bin/pip install dist/*.whl

ARG BRANCH_NAME=Local
ARG COMMIT_HASH=unknown
RUN echo "Branch: $BRANCH_NAME, Commit: $COMMIT_HASH" && \
    echo "SOPHIE_COMMIT = \"$COMMIT_HASH\"" >> /build/sophie_bot/versions.py && \
    echo "SOPHIE_BRANCH = \"$BRANCH_NAME\"" >> /build/sophie_bot/versions.py


FROM python:3.13-slim as final

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

RUN apt update && \
    apt install -y --no-install-recommends libicu-dev && \
    rm -rf /var/lib/apt/lists/*

# RUN apk add --no-cache libffi libpq

COPY --from=builder /venv /venv
COPY --from=builder /build/sophie_bot /sophie_bot

COPY --from=builder /build/locales /locales

WORKDIR /

ENTRYPOINT ["/venv/bin/python", "-m", "sophie_bot"]
CMD ["bot"]
