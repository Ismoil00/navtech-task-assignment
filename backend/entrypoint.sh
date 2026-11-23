#!/bin/sh
set -e

# Если передана команда (например, `docker compose run --rm backend pytest`),
# выполняем её вместо запуска сервера.
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

echo "Применяю миграции БД..."
alembic upgrade head

if [ "${SEED_DEMO_USERS:-false}" = "true" ]; then
    echo "Создаю демо-пользователей..."
    python -m scripts.seed
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
