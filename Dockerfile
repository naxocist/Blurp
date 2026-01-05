FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
  make \
  libgl1 \
  libglib2.0-0 \
  curl \
  wget \
  && rm -rf /var/lib/apt/lists/* \
  && (curl -Ls --tlsv1.2 --proto "=https" --retry 3 https://cli.doppler.com/install.sh \
  || wget -t 3 -qO- https://cli.doppler.com/install.sh) | sh

COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/


WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD ps aux | grep "[p]ython" || exit 1

CMD [ "doppler", "run", "--", "make", "run-prod" ]

