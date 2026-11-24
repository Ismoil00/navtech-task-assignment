#!/bin/sh
set -e

# Адрес API подставляется при старте контейнера из переменной окружения,
# поэтому один и тот же образ работает с любым backend без пересборки.
cat > /usr/share/nginx/html/config.js <<CONFIG
window.__APP_CONFIG__ = { apiUrl: "${FRONTEND_API_URL:-http://localhost:8000/api}" };
CONFIG

echo "config.js: apiUrl=${FRONTEND_API_URL:-http://localhost:8000/api}"
