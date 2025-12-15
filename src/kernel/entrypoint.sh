#!/bin/sh
set -e

PROJECT_DIR="/app/src/kernel"

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "Running migrations..."
  python "$PROJECT_DIR/manage.py" migrate --noinput
  python "$PROJECT_DIR/manage.py" csu
fi

if [ "$#" -gt 0 ]; then
  cd "$PROJECT_DIR"
  exec "$@"
fi

cd "$PROJECT_DIR"
exec gunicorn kernel.wsgi:application --bind 0.0.0.0:8000
