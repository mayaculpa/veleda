#!/bin/bash

# Exit with nonzero exit code if anything fails
set -e

# Need the sleep to wait for postgres to start
# Should use pg_isready https://stackoverflow.com/a/42225536/6783666
echo "Waiting PostgreSQL to launch on 5432..."

while ! nc -z postgres 5432; do
  echo "Waiting..."
  sleep 0.5 # wait for 1/10 of the second before check again
done

# Migrate the database to the newest version
./manage.py migrate

# Check and create admin user
if [ -z "$ADMIN_EMAIL" ]; then
    echo "Missing ADMIN_EMAIL"
    exit 1
fi
if [ -z "$ADMIN_PASSWORD" ]; then
    echo "Missing ADMIN_PASSWORD"
    exit 1
fi

echo "from django.contrib.auth import get_user_model; \
      User = get_user_model(); \
      User.objects.create_superuser('$ADMIN_EMAIL', '$ADMIN_PASSWORD')" \
      | python manage.py shell

# Start Gunicorn processes
echo Starting Gunicorn.
exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3

