#!/bin/bash

# Exit with nonzero exit code if anything fails
set -e

# Need the sleep to wait for postgres to start
# Should use pg_isready https://stackoverflow.com/a/42225536/6783666

echo "Waiting PostgreSQL to launch on 5432..."
while ! nc -z postgres 5432; do
  echo "Waiting..."
  sleep 0.5 # wait for half a second before checking again
done

echo "Waiting for RabbitMQ to launch on 5672..."
while ! nc -z rabbitmq 5672; do
  echo "Waiting..."
  sleep 0.5 # wait for half a second before checking again
done

# Migrate the database to the newest version
pipenv run ./manage.py migrate

# Start Celery worker processes
echo "Starting Celery processes"
pipenv run celery -A core worker -l info &

# Start Gunicorn processes
echo "Starting Gunicorn."
exec pipenv run gunicorn core.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3
    --capture-output
    --enable-stdio-inheritance

