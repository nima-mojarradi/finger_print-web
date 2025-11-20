#!/bin/sh
mkdir -p /app/data

echo "Applying database migrations..."
python manage.py migrate

exec "$@"