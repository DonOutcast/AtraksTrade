FROM python:3.12-slim-bookworm AS build

RUN mkdir /app
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libffi-dev libpq-dev liblz4-dev libunwind-dev && \
    pip install --upgrade pip poetry && \
    rm -rf /var/lib/apt/lists/*

RUN python -m venv /env
ENV VIRTUAL_ENV=/env
ENV PATH="/env/bin:$PATH"

COPY src/pyproject.toml src/poetry.lock ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi

FROM python:3.12-slim-bookworm AS development
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
  && rm -rf /var/lib/apt/lists/*

COPY --from=build /env /env
ENV VIRTUAL_ENV=/env
ENV PATH="/env/bin:$PATH"

COPY . .

COPY src/kernel/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
