FROM python:3.12-slim as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt update
RUN apt install build-essential gcc git -y
RUN pip install poetry wheel
RUN python -m venv /venv

RUN poetry self add poetry-plugin-export

WORKDIR /build
COPY ../../pyproject.toml poetry.lock ./

RUN poetry export -f requirements.txt -E fast --without-hashes | /venv/bin/pip install -r /dev/stdin

COPY ../../sophie_bot sophie_bot
COPY ../../locales locales
COPY ../../Makefile Makefile

RUN bash -c "source /venv/bin/activate; make new_lang=en_US; make compile_lang"

RUN poetry build && /venv/bin/pip install dist/*.whl

COPY ../../.git .git
RUN BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD) && \
    COMMIT_HASH=$(git rev-parse --short HEAD) && \
    echo "Branch: $BRANCH_NAME, Commit: $COMMIT_HASH" && \
    echo "SOPHIE_COMMIT = \"$COMMIT_HASH\"" >> /build/sophie_bot/versions.py && \
    echo "SOPHIE_BRANCH = \"$BRANCH_NAME\"" >> /build/sophie_bot/versions.py


FROM python:3.12-slim as final

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

# RUN apk add --no-cache libffi libpq

COPY --from=builder /venv /venv
COPY --from=builder /build/sophie_bot /sophie_bot

COPY --from=builder /build/locales /locales

WORKDIR /

ENTRYPOINT ["/venv/bin/python", "-m", "sophie_bot"]
CMD ["bot"]
