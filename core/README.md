# Core Service

## Installation

The Django application is responisble for the user authentication.

Local install requires *Docker* and the following commands:

    sudo apt install python3-pip libpq-dev
    python3 -m pip install --user pipenv
    pipenv install
    pipenv shell

Start with:

    ./start.sh

This starts a development environment by default. If `DJANGO_DEBUG=False` is set, the production environment will be loaded. This variable is loaded if started via the docker compose command.

### Server Domain

In order to create the farm subdomains, the server domain and the subdomain namespace have to be known (e.g., *example.com* and *farms*). The namespace will be slugified (i.e., only alphanumerics, underscores and hyphens). Set both variables in the `dns.core` file.

## Tests

The tests try to mirror the production environment throught the use of the respective Docker services. The command to run tests:

    ./start.sh test

The command to create an HTML report of the test coverage:

    ./start.sh coverage

### Running Celery Tasks

A Celery task runner and RabbitMQ Docker service are created by default when running `start.sh`.

## Database Migrations

For a database migration, the web app has to be started outside Docker (the database may run in Docker). First make sure the database is up-to-date:

    ./start.sh makemigrations

The `migrate` command is called by default by the `start.sh` script

# Save and Load Seed Data

To save the current state of the database to a file:

    ./start.sh dumpdata /path/to/db_seed.json

To load the saved data into a database:

    ./start.sh loaddata /path/to/db_seed.json

## Options

To start the web server with a custom port and host binding:

    ./start.sh runserver 0.0.0.0:8001

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
5. Set the client type and authorization grant type (*Confidential* and *Authorization Code*)
6. Add the redirect URI from the `grafana/secrets.grafana` file
7. Save the new OAuth2 application
8. Go to the Admin Dashboard (https://core.openfarming.ai/admin/)
9. Go to the new application (Oauth2_Provider --> Applications --> *Application Name*)
10. Enable *Skip authorization* at the bottom of the page
11. Save the changes

To start a NodeRED instance (part of the sdg-coordinator), start the following Docker service:

    docker run -it --rm --network host -v /path/to/sdg-coordinator/node-red/settings.js:/data/settings.js --name mynodered nodered/node-red

To register a NodeRED application
1. Go to the OAuth2 Dashboard (https://core.openfarming.ai/o/applications/)
2. Click the link to register a new application
3. Type in an application name
4. Copy the client ID and secret into the `Secrets` node on the `SDG Login` tab
5. Set the client type: *Confidential* and authorization grant type: *Resource owner password-based / password*
6. Save the new OAuth2 application
