#! /bin/bash

# Need the sleep to wait for postgres to start
# Should use pg_isready https://stackoverflow.com/a/42225536/6783666
echo "Waiting PostgreSQL to launch on 5432..."

while ! nc -z postgres 5432; do
  echo "Waiting..."
  sleep 0.5 # wait for 1/10 of the second before check again
done

python manage.py db upgrade
python manage.py setup_prod
gunicorn --bind=0.0.0.0:8000 --workers=3 --log-level=INFO manage:app &
python -u manage.py run_worker
