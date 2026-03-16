#!/bin/bash
set -e

echo "[entrypoint] Running Django migrations..."
python manage.py migrate --noinput

# If arguments were passed (e.g. celery worker), exec them.
# Otherwise default to the Daphne ASGI server.
if [ $# -gt 0 ]; then
    exec "$@"
else
    echo "[entrypoint] Starting Daphne ASGI server..."
    exec daphne -b 0.0.0.0 -p 8000 core.asgi:application
fi
