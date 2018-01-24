[![Build Status](https://travis-ci.org/mayaculpa/veleda.svg?branch=master)](https://travis-ci.org/mayaculpa/veleda)

# Veleda

## Docker Compose

Start the complete setup with:

    docker-compose build && docker-compose up -d

Stop the setup with:

    docker-compose down

The individual services can be reached on the following ports:

| Name     | Purpose              | Port |
| -------- | -------------------- | ---- |
| web      | User management      | 8001 |
| postgres | User storage         | 5431 |
| redis    | Async task storage   | 6379 |
| influxdb | Time series storage  | 8086 |
| grafana  | Time series analysis | 3000 |

## Web

The web app is based on the Flask framework and is responisble for the user authentication.

Local install:

    virtualenv venv
    source venv/bin/activate
    pip install --no-cache-dir -r requirements.txt

Start with:

    gunicorn manage:app

or

    python -u manage.py runserver

For more information, see the [web readme](web/README.md)
