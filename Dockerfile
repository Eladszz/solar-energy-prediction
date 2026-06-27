# Build the React frontend assets first.
FROM node:20-slim AS frontend-builder

WORKDIR /app/solar_frontend

COPY solar_frontend/package.json solar_frontend/package-lock.json ./
RUN npm ci

COPY solar_frontend ./
COPY shared /app/shared
RUN npm run build


# Runtime image for the FastAPI backend and built frontend bundle.
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY solar_backend/backend_requirements.txt /app/backend_requirements.txt
RUN pip install --no-cache-dir -r backend_requirements.txt

COPY solar_backend /app/solar_backend
COPY shared /app/shared
COPY --from=frontend-builder /app/solar_frontend/dist /app/solar_frontend/dist
COPY docker/start.sh /app/start.sh

RUN mkdir -p /app/solar_backend/logs \
    && chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
