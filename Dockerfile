FROM node:22-bookworm-slim AS assets
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY everwealth/static ./everwealth/static
COPY everwealth/templates ./everwealth/templates
RUN npm run build

FROM python:3.12-slim-bookworm AS dependencies
WORKDIR /app
COPY pyproject.toml README.md ./
COPY vendor ./vendor
COPY everwealth ./everwealth
RUN pip install --no-cache-dir --prefix=/install .

FROM ghcr.io/amacneil/dbmate:2.28.0 AS dbmate

FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000
WORKDIR /app
COPY --from=dependencies /install /usr/local
COPY --from=dbmate /usr/local/bin/dbmate /usr/local/bin/dbmate
COPY everwealth ./everwealth
COPY --from=assets /app/everwealth/static/styles.css ./everwealth/static/styles.css
COPY --from=assets /app/everwealth/static/scripts/app.js ./everwealth/static/scripts/app.js
COPY db/migrations ./db/migrations
COPY scripts ./scripts
RUN useradd --create-home --uid 10001 app
USER app
EXPOSE 8000
CMD ["sh", "scripts/start.sh"]
