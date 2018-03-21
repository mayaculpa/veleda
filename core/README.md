# Flask Web Application

## Installation

The web app is based on the Flask framework and is responisble for the user authentication.

Local install:

    virtualenv venv
    source venv/bin/activate
    pip install --no-cache-dir -r requirements.txt

Start with:

    gunicorn manage:app

or

    python -u manage.py runserver

## Tests

The command to run tests:

    pip install -r requirements-test.txt
    python -u manage.py test

The command to create an HTML report of the test coverage:

    coverage html

## Local Development

Set `FLASK_CONFIG` to `development` and extend the secrets file with:

    GF_AUTH_GENERIC_OAUTH_CLIENT_ID=ab12
    GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET=secret
    GRAFANA_REDIRECT_URI=http://localhost:3000/login/generic_oauth
    GRAFANA_SCOPES=email

Create a development database (SQLite) with:

    python -u manage.py recreate_db

Then start the development server. Changes to the code are automatically reloaded

    python -u manage.py runserver

## Database Migrations

For a database migration, the web app has to be started outside Docker (the database may run in Docker). First make sure the database is up-to-date:

    python manage.py db upgrade

Then, to create a new migration use:

    python manage.py db migrate

This will create a diff from the previous database in migrations/versions.

## Options

To start the web server with a custom port and host binding:

    python -u manage.py runserver -p 8001 -h 0.0.0.0

## Recommended Development Process

The secret configuration differs when using local and Docker configurations.