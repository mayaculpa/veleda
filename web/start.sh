#! /bin/bash

# Need the sleep to wait for postgres to start
sleep 1

python manage.py db upgrade
python manage.py setup_prod
gunicorn --bind=0.0.0.0:8001 --workers=3 manage:app
