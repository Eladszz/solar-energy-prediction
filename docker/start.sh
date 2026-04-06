#!/bin/sh
set -eu

cd /app/solar_backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
backend_pid=$!

python3 -m http.server 3000 --directory /app/solar_frontend/dist &
frontend_pid=$!

cleanup() {
  kill "$backend_pid" "$frontend_pid" 2>/dev/null || true
}

trap cleanup INT TERM

while kill -0 "$backend_pid" 2>/dev/null && kill -0 "$frontend_pid" 2>/dev/null; do
  sleep 1
done

cleanup
wait "$backend_pid" "$frontend_pid" 2>/dev/null || true
