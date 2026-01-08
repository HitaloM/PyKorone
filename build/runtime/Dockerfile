FROM python:3.13-slim as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt update
RUN apt install -y build-essential gcc git pkg-config libicu-dev
RUN pip install uv
RUN python -m venv /venv

WORKDIR /build
COPY pyproject.toml uv.lock ./

RUN uv export --format requirements.txt | /venv/bin/pip install -r /dev/stdin

COPY sophie_bot sophie_bot
COPY locales locales
COPY Makefile Makefile

# Install dependencies and setup locale
RUN bash -c "source /venv/bin/activate && \
    /venv/bin/pip install Babel && \
    export PATH=/venv/bin:\$PATH && \
    make new_lang=en_US && \
    make compile_lang"

RUN uv build --wheel && /venv/bin/pip install dist/*.whl

COPY .git .git
RUN BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD) && \
    COMMIT_HASH=$(git rev-parse --short HEAD) && \
    echo "Branch: $BRANCH_NAME, Commit: $COMMIT_HASH" && \
    echo "SOPHIE_COMMIT = \"$COMMIT_HASH\"" >> /build/sophie_bot/versions.py && \
    echo "SOPHIE_BRANCH = \"$BRANCH_NAME\"" >> /build/sophie_bot/versions.py


FROM python:3.13-slim as final

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

RUN apt update
RUN apt install -y libicu-dev

# RUN apk add --no-cache libffi libpq

COPY --from=builder /venv /venv
COPY --from=builder /build/sophie_bot /sophie_bot

COPY --from=builder /build/locales /locales

WORKDIR /

ENTRYPOINT ["/venv/bin/python", "-m", "sophie_bot"]
CMD ["bot"]
