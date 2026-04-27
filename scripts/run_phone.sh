#!/usr/bin/env bash
set -euo pipefail

HOST_IP=$(hostname -I | awk '{print $1}')
PORT=${1:-8000}

echo "Starting server on 0.0.0.0:${PORT}"
echo "Open on your phone (same Wi-Fi): http://${HOST_IP}:${PORT}"
uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
