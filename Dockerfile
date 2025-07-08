FROM python:3.12-slim-bookworm AS base

FROM base AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY uv.lock pyproject.toml /app/

RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-install-project --no-dev

COPY src /app
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev

FROM base AS runner

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN useradd -m -r appuser && \
    mkdir /app && \
    chown -R appuser /app

WORKDIR /app

COPY --from=builder --chown=appuser:appuser  /app /app
ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8000
CMD ["uvicorn", "murmur.asgi:application", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS dev-runner

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN useradd -m -r appuser && \
    mkdir /app && \
    chown -R appuser /app

WORKDIR /app

COPY --from=builder --chown=appuser:appuser  /app /app
ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8000
CMD ["uvicorn", "murmur.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "src"]
