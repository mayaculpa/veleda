#!/bin/bash

function finish {
  # Kills all forked processes (Celery worker)
  pkill -P $$
}
trap finish EXIT

# Exit with nonzero exit code if anything fails
set -e

DATABASE_HOST="postgres"
RABBITMQ_HOST="rabbitmq"
GUNICORN_HOST="0.0.0.0"

# Source and export all required env variables from the respective files
# for local development
source_debug_env_variables() {
  set -a # Set all sourced envs to be exported

  echo "Sourcing debug env variables"
  source ./env.core
  source ./secrets.core
  source ./env.rabbitmq
  source ./secrets.rabbitmq
  DJANGO_DEBUG=True
  
  echo "Updating postgres and rabbitmq hostnames to localhost"
  export DATABASE_HOST="127.0.0.1"
  export RABBITMQ_HOST="127.0.0.1"
  export GUNICORN_HOST="127.0.0.1"
  
  set +a
}

start_docker_services() {
  echo "Starting dev databases. Removed on container stop"
  if [[ ! "$(docker ps -a | grep sdg-server-dev-postgres)" ]]; then
    echo "Starting PostgreSQL docker service"
    docker run \
      --rm \
      --name sdg-server-dev-postgres \
      -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
      -p $DATABASE_HOST:5432:5432 \
      -d \
      postgres:10.2
    # Flag for seeding the database with dummy data
    EMPTY_DB=1
  else
    echo "PostgreSQL docker service already running"
  fi
  if [[ ! "$(docker ps -a | grep sdg-server-dev-rabbitmq)" ]]; then
    echo "Starting RabbitMQ docker service"
    docker run \
      --rm \
      --name sdg-server-dev-rabbitmq \
      -p $RABBITMQ_HOST:5672:5672 \
      -d \
      rabbitmq:3
  else
    echo "RabbitMQ docker service already running"
  fi
}

if [[ $DJANGO_DEBUG != "False" ]]; then
  source_debug_env_variables
  start_docker_services
fi

echo "Waiting for PostgreSQL to launch on $DATABASE_HOST:5432..."
while ! pg_isready -h "$DATABASE_HOST" -q; do
  echo "Waiting..."
  sleep 0.5 # wait for half a second before checking again
done

if [[ $DJANGO_DEBUG != "False" ]]; then
  # Source and rename the password for the postgres user (superuser)
  source ../postgres/secrets.postgres
  PGPASSWORD=$POSTGRES_PASSWORD

  if [[ $( psql -U postgres -h localhost -tAc "SELECT 1 FROM pg_database WHERE datname='$DATABASE_NAME'" ) != '1' ]]; then
    echo "Creating core database and user in PostgreSQL"
    psql -U postgres -h localhost -c \
      "CREATE DATABASE $DATABASE_NAME WITH ENCODING 'UTF8';"
    psql -U postgres -h localhost -c \
      "CREATE USER $DATABASE_USER ENCRYPTED PASSWORD '$DATABASE_PASSWORD' NOSUPERUSER NOCREATEDB NOCREATEROLE;"
    psql -U postgres -h localhost -c \
      "GRANT ALL PRIVILEGES ON DATABASE $DATABASE_NAME TO $DATABASE_USER;"
  fi
fi

echo "Waiting for RabbitMQ to launch on 5672..."
while ! nc -z $RABBITMQ_HOST 5672; do
  echo "Waiting..."
  sleep 0.5 # wait for half a second before checking again
done

# Migrate the database and seed values for new dev databases
echo "Performing database migration"
pipenv run ./manage.py migrate
if [[ $DJANGO_DEBUG != "FALSE" && EMPTY_DB -eq 1 ]]; then
  echo "Seeding DB with data"
  pipenv run ./manage.py loaddata db_seed.json
fi

if [[ $(./manage.py createsuperuser --no-input >/dev/null 2>&1) ]]; then
  echo "Creating superuser $DJANGO_SUPERUSER_EMAIL"
else
  echo "Superuser $DJANGO_SUPERUSER_EMAIL already exists"
fi

echo "Starting Celery processes"
pipenv run celery -A core worker -l info &

if [[ -z $1 ]]; then
  # Start the app server, either for the dev or prod environment
  if [[ $DJANGO_DEBUG != "FALSE" ]]; then
    echo "Starting Django dev server"
    pipenv run ./manage.py runserver
  else
    echo "Starting Gunicorn"
    exec pipenv run gunicorn core.wsgi:application \
        --bind "$GUNICORN_HOST:8000" \
        --workers 3
        --capture-output
        --enable-stdio-inheritance
  fi
elif [[ $1 == "test" ]]; then
  echo "Starting Django test runner"
  pipenv run ./manage.py test $2
elif [[ $1 == "coverage" ]]; then
  echo "Starting test coverage analysis"
  pipenv run coverage run --source='.' manage.py test
  pipenv run coverage html
  DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
  echo "Coverage analysis created: file:$DIR/htmlcov/index.html"
elif [[ $1 == "dumpdata" ]]; then
  if [[ -z $2 ]]; then
    echo "Missing file name"
    exit 1
  fi
  echo "Dumping database to $2"
  pipenv run ./manage.py dumpdata > "$2"
elif [[ $1 == "loaddata" ]]; then
  if [[ -z $2 ]]; then
    echo "Missing file name"
    exit 1
  fi
  echo "Loading database from $2"
  pipenv run ./manage.py loaddata "$2"
else
  echo "$@"
  pipenv run ./manage.py "$@"
fi
