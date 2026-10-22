# The read-only TSI API (deployed on Render; build context = backend/).
# Only DATABASE_URL and TSI_CORS_ORIGINS are needed at runtime; no CFBD key.
FROM python:3.12.15-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first (cached until pyproject/uv.lock change), then the project itself.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev

RUN useradd --system --no-create-home tsi
USER tsi

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
# Render sets PORT; default 8000 elsewhere.
CMD ["sh", "-c", "exec tsi serve --host 0.0.0.0 --port ${PORT:-8000}"]
