FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    make \
    && rm -rf /var/lib/apt/lists/*

COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/


WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .

RUN uv sync --frozen

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD ps aux | grep "[p]ython" || exit 1

CMD [ "make", "run-prod" ]

