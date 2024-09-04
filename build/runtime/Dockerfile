FROM python:3.12-slim as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt update
RUN apt install build-essential gcc -y
RUN pip install poetry wheel
RUN python -m venv /venv

WORKDIR /build
COPY ../../pyproject.toml poetry.lock ./

RUN poetry export -f requirements.txt -E fast --without-hashes | /venv/bin/pip install -r /dev/stdin

COPY ../../sophie_bot sophie_bot
COPY ../../locales locales
COPY ../../Makefile Makefile

RUN bash -c "source /venv/bin/activate; make compile_lang"

RUN poetry build && /venv/bin/pip install dist/*.whl

FROM python:3.12-slim as final

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

# RUN apk add --no-cache libffi libpq

COPY --from=builder /venv /venv
COPY ../../sophie_bot /sophie_bot

COPY --from=builder /build/locales /locales

WORKDIR /

CMD ["/venv/bin/python", "-m", "sophie_bot"]
