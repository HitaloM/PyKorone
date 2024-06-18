FROM python:3.11-slim AS builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt update
RUN apt install build-essential gcc -y
RUN pip install poetry wheel
RUN python -m venv /venv


WORKDIR /build
COPY ../../pyproject.toml poetry.lock ./

RUN poetry export -f requirements.txt -E fast --without-hashes
RUN poetry export -f requirements.txt -E fast --without-hashes | /venv/bin/pip install -r /dev/stdin

COPY ../../Makefile Makefile

COPY ../../app app
COPY ../../locales locales

RUN bash -c "source /venv/bin/activate; make new_locale"

RUN pwd



FROM python:3.11-slim AS final

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

# RUN apk add --no-cache libffi libpq

COPY --from=builder /venv /venv
COPY ../../app /app
COPY ../../migrations /migrations

COPY --from=builder /build/locales /locales

WORKDIR /

CMD ["/venv/bin/python", "-m", "app"]
