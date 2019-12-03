# Core Service

## Installation

The Django application is responisble for the user authentication.

Local install:

    pip install --user pipenv
    pipenv install
    pipenv shell

Start with:

    ./start.sh

Or

    ./manage.py migrate
    ./manage.py runserver

### Server Domain

In order to create the farm subdomains, the server domain and the subdomain namespace have to be known (e.g., *example.com* and *farms*). The namespace will be slugified (i.e., only alphanumerics, underscores and hyphens). Set both variables in the `dns.core` file.

## Tests

The command to run tests:

    ./manage.py test

The command to create an HTML report of the test coverage:

    coverage run --source='.' manage.py test
    coverage html

## Local Development

Create a development database (SQLite) and a superuser with:

    ./manage.py migrate
    ./manage.py createsuperuser

Then start the development server. Changes to the code are automatically reloaded

    ./manage.py runserver

### Running Celery Tasks

This requires RabbitMQ and Celery to be started before the `./manage.py runserver` command is run.

    docker run -d --hostname my-rabbit -p 127.0.0.1:5672:5672 --name some-rabbit rabbitmq:3
    celery -A core worker -l info

## Database Migrations

For a database migration, the web app has to be started outside Docker (the database may run in Docker). First make sure the database is up-to-date:

    ./manage.py makemigrations

Then, to create a new migration use:

    ./manage.py migrate

This will create a diff from the previous database in migrations/versions.

## Options

To start the web server with a custom port and host binding:

    ./manage.py runserver -p 8001 -h 0.0.0.0

## Running a local Docker instance

To enable DNS and subdomains add the following entries to your `/etc/hosts` file

    # Used for development of the SDG server
    127.0.0.1       data.sdg.local
    127.0.0.1       core.sdg.local
    127.0.0.1       sdg.local
    127.0.0.1       www.sdg.local

Then create a `dns.core` file with the entry

    VIRTUAL_HOST=core.sdg.local

Subsequently, from the repository root directory start all Docker containers with

    docker-compose build && docker-compose up -d

To create a super-user in the core docker container run

    docker exec -it core bash
    ./manage.py createsuperuser

To register a new OAuth2 application (such as Grafana)
1. Go to the OAuth2 Dashboard (https://core.openfarming.ai/o/applications/)
2. Click the link to register a new application
3. Type in an application name
4. Copy the client ID and secret into the `grafana/secrets.grafana` file
5. Set the client type and authorization grant type (usually *Confidential* and *Authorization Code*)
6. Add the redirect URI from the `grafana/secrets.grafana` file
7. Save the new OAuth2 application
8. Go to the Admin Dashboard (https://core.openfarming.ai/admin/)
9. Go to the new application (Oauth2_Provider --> Applications --> *Application Name*)
10. Enable *Skip authorization* at the bottom of the page
11. Save the changes
