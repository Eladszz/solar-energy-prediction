# Build the React frontend assets first.
FROM node:20-slim AS frontend-builder

WORKDIR /app/solar_frontend

COPY solar_frontend/package.json solar_frontend/package-lock.json ./
RUN npm ci

COPY solar_frontend ./
RUN npm run build


# Runtime image for the FastAPI backend and built frontend bundle.
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY solar_backend/backend_requirements.txt /app/backend_requirements.txt
RUN pip install --no-cache-dir -r backend_requirements.txt

COPY solar_backend /app/solar_backend
COPY --from=frontend-builder /app/solar_frontend/dist /app/solar_frontend/dist
COPY docker/start.sh /app/start.sh

RUN mkdir -p /app/solar_backend/logs \
    && chmod +x /app/start.sh

# 8000 for FastAPI backend
# 3000 for the built React frontend
EXPOSE 8000 3000

CMD ["/app/start.sh"]
