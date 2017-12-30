# Thyme Data

## Docker Compose

Start the complete setup with:

    docker-compose up -d

Stop the setup with:

    docker-compose down

## Web

The web app is based on the Flask framework and is responisble for the user authentication.

Local install:

    virtualenv venv
    source venv/bin/activate
    pip install --no-cache-dir -r requirements.txt

Start with:

    gunicorn manage:app

or

    python -u manage.py webserver

