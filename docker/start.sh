#!/bin/sh
set -eu

PORT="${PORT:-8000}"

cd /app/solar_backend
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
