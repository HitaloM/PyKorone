# Build stage - uses uv pre-installed Python image
FROM ghcr.io/astral-sh/uv:0.9.26-python3.13-bookworm-slim AS builder

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1
# Copy from cache instead of linking (required for cache mounts)
ENV UV_LINK_MODE=copy
# Omit development dependencies
ENV UV_NO_DEV=1
# Ensure installed tools are accessible
ENV UV_TOOL_BIN_DIR=/usr/local/bin

WORKDIR /app

# Copy dependency files first for optimal layer caching
COPY pyproject.toml uv.lock ./
COPY libs libs

# Install dependencies first (without the project itself)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --compile-bytecode

# Copy the project source code
COPY sophie_bot sophie_bot
COPY locales locales
COPY Makefile Makefile

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --compile-bytecode

# Compile translations
RUN uv run --no-sync pybabel compile -d locales -D sophie --use-fuzzy --statistics

# Inject version information
ARG BRANCH_NAME=Local
ARG COMMIT_HASH=unknown
RUN SOPHIE_VERSION=$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])") && \
    echo "SOPHIE_VERSION = \"$SOPHIE_VERSION\"" > /app/sophie_bot/versions.py && \
    echo "SOPHIE_COMMIT = \"$COMMIT_HASH\"" >> /app/sophie_bot/versions.py && \
    echo "SOPHIE_BRANCH = \"$BRANCH_NAME\"" >> /app/sophie_bot/versions.py

# Runtime stage - minimal image without uv
FROM python:3.13-slim-bookworm

# Setup non-root user for security
RUN groupadd --system --gid 999 sophie && \
    useradd --system --gid 999 --uid 999 --create-home sophie

# Python runtime settings
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends libicu-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy the virtualenv from builder (contains all dependencies)
COPY --from=builder --chown=sophie:sophie /app/.venv /app/.venv

# Copy application source code and assets (editable install references these)
COPY --from=builder --chown=sophie:sophie /app/sophie_bot /app/sophie_bot
COPY --from=builder --chown=sophie:sophie /app/locales /app/locales

# Place virtualenv at the front of PATH
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Switch to non-root user
USER sophie

# Run the application directly (no uv needed at runtime)
CMD ["python", "-m", "sophie_bot"]
