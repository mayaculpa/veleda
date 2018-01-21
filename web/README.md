# Flask Web Application

To setup your environment:

    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt

## Tests

The command to run tests:

    pip install -r requirements-test.txt
    python -u manage.py test

The command to calculate the line coverage:

    coverage html

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

To increase the logging level add the following code to the Config class

    import logging
    logging.basicConfig(level=logging.DEBUG)