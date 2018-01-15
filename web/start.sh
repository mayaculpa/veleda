#! /bin/bash

# Need the sleep to wait for postgres to start
# Should use pg_isready https://stackoverflow.com/a/42225536/6783666
sleep 1

export FLASK_CONFIG=production
python manage.py db upgrade
python manage.py setup_prod
gunicorn --bind=0.0.0.0:8001 --workers=3 manage:app &
python -u manage.py run_worker
