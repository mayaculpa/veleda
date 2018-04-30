# Flask Web Application

## Installation

The web app is based on the Flask framework and is responisble for the user authentication.

Local install:

    virtualenv -p python3 venv
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

    coverage run --source=app manage.py test
    coverage html

Integration tests are also available that test InfluxDB. To run them add `INTEGRATION_TESTS=True` to `secrets.core`

## Local Development

Set `FLASK_CONFIG` to `development` and extend the secrets file with the following. The *GF* prefixed variables are used directly by Grafana. The *GRAFANA* prefix is used by the *core* component to interact with Grafana. The prefix *INFLUXDB* denotes variables used by InfluxDB.

    GF_AUTH_GENERIC_OAUTH_CLIENT_ID=ab12
    GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET=secret
    GRAFANA_REDIRECT_URI=http://localhost:3000/login/generic_oauth
    GF_AUTH_GENERIC_OAUTH_SCOPES=email

    INFLUXDB_ADMIN_USER=admin
    INFLUXDB_ADMIN_PASSWORD=SuperS3cretPassword

Create a development database (SQLite) with:

    python -u manage.py recreate_db

Then start the development server. Changes to the code are automatically reloaded

    python -u manage.py runserver

## Database Migrations

For a database migration, the web app has to be started outside Docker (the database may run in Docker). First make sure the database is up-to-date:

    python manage.py db upgrade

Then, to create a new migration use:

    python manage.py db migrate

This will create a diff from the previous database in migrations/versions. Note that SQLite is *not* supported. For development that does not require schema changes, i.e., no changes or new models, SQLite may be used.

## Options

To start the web server with a custom port and host binding:

    python -u manage.py runserver -p 8001 -h 0.0.0.0

## Upgrading Semantic-UI

The [Semantic-UI][1] is used for web icons and flags. For a list of all available icons, visit their [icon page][2]. To upgrade Semantic-UI, download the [latest pre-compiled artefact][3]. Extract the following files to their appropriate locations:

- `semantic.min.js` to `app/assets/scripts/vendor`
- `semantic.css` to `app/assets/styles/vendor`
- `themes/default/assets/images/` to `app/static/images/vendor/semantic`
- `themes/default/assets/fonts/` to `app/static/fonts/vendor/semantic`

Then, in `semantic.css` replace:

- `./themes/default/assets/images` with `../images/vendor/semantic/`
- `./themes/default/assets/fonts/` with `../fonts/vendor/semantic/`

## Recommended Development Process

The secret configuration differs when using local and Docker configurations.


[1]: https://semantic-ui.com/
[2]: https://semantic-ui.com/elements/icon.html
[3]: https://github.com/Semantic-Org/Semantic-UI-CSS/archive/master.zip
