#!/bin/sh

# entrypoint.sh

echo "Waiting for database to be ready..."
# یک تاخیر ساده به جای nc
sleep 10

echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000
