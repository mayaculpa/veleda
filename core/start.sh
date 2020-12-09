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
DAPHNE_HOST="0.0.0.0"
REDIS_HOST="redis"

print_help() {
  printf "%s\n" \
"Commands:
  [none]      Start dev server (Default)
  test        Run tests (takes standard Django manage.py test arguments)
  coverage    Create test coverage in htmlcov folder
  shell       Creates a Django shell
  clean       Remove docker services. Useful to reload DB seed data
  dumpdata    Dumps PostgreSQL data to JSON file
  loaddata    Loads data dump into PostgreSQL
  pytest      Run pytests (Depreciated)
  help        Print help

Unknown commands will be passed to ./manage.py as parameters. DB seed data is
loaded on first creation of the PostgreSQL database."
}

# Source and export all required env variables from the respective files
# for local development
source_debug_env_variables() {
  set -a # Set all sourced envs to be exported

  echo "Sourcing debug env variables"
  source ./env.core
  source ./secrets.core
  source ./env.rabbitmq
  source ./secrets.rabbitmq
  source ../postgres/secrets.postgres
  source ../redis/env.redis
  source ../redis/secrets.redis
  DJANGO_DEBUG=True
  
  echo "Updating the service hostnames to localhost"
  export DATABASE_HOST="127.0.0.1"
  export RABBITMQ_HOST="127.0.0.1"
  export DAPHNE_HOST="$CORE_DOMAIN"
  export REDIS_HOST="127.0.0.1"
  
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
      timescale/timescaledb:latest-pg12
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
  if [[ ! "$(docker ps -a | grep sdg-server-dev-redis)" ]]; then
    echo "Starting Redis docker service"
    docker run \
      --rm \
      --name sdg-server-dev-redis \
      -p $REDIS_HOST:6379:6379 \
      -d \
      redis:5 \
      "redis-server" "--requirepass" "$REDIS_PASSWORD"
  else
    echo "Redis docker service already running"
  fi
}

stop_docker_services() {
  echo "Stopping dev databases"
  if [[ "$(docker ps -a | grep sdg-server-dev-postgres)" ]]; then
    docker stop sdg-server-dev-postgres
  else
    echo "Postgres database already stopped"
  fi
  if [[ "$(docker ps -a | grep sdg-server-dev-rabbitmq)" ]]; then
    docker stop sdg-server-dev-rabbitmq
  else
    echo "RabbitMQ database already stopped"
  fi
  if [[ "$(docker ps -a | grep sdg-server-dev-redis)" ]]; then
    docker stop sdg-server-dev-redis
  else
    echo "Redis database already stopped"
  fi
}

if [[ $1 == "help" ]]; then
  print_help
  exit 0
fi

if [[ $DJANGO_DEBUG != "False" ]]; then
  if [[ $1 == "clean" ]]; then
    stop_docker_services
    set +e
    exit 0
  else
    echo "Starting in debug mode"
    source_debug_env_variables
    start_docker_services
  fi
else
  echo "Starting in production mode"
fi

echo "Waiting for PostgreSQL to launch on $DATABASE_HOST:5432..."
while ! pg_isready -h "$DATABASE_HOST" -q; do
  echo "Waiting..."
  sleep 0.5 # wait for half a second before checking again
done

export PGPASSWORD=$POSTGRES_PASSWORD
if [[ $( psql -U postgres -h $DATABASE_HOST -tAc "SELECT 1 FROM pg_database WHERE datname='$DATABASE_NAME'" ) != '1' ]]; then
  echo "Creating core database and user in PostgreSQL"
  psql -U postgres -h $DATABASE_HOST -c \
    "CREATE DATABASE $DATABASE_NAME WITH ENCODING 'UTF8';"
  psql -U postgres -h $DATABASE_HOST -c \
    "CREATE USER $DATABASE_USER ENCRYPTED PASSWORD '$DATABASE_PASSWORD' NOSUPERUSER NOCREATEDB NOCREATEROLE;"
  psql -U postgres -h $DATABASE_HOST -c \
    "GRANT ALL PRIVILEGES ON DATABASE $DATABASE_NAME TO $DATABASE_USER;"
else
  echo "$DATABASE_NAME already created on $DATABASE_HOST Postgres DB"
fi

echo "Waiting for RabbitMQ to launch on 5672..."
while ! nc -z $RABBITMQ_HOST 5672; do
  echo "Waiting..."
  sleep 0.5 # wait for half a second before checking again
done

echo "Waiting for Redis to launch on 6379..."
while ! nc -z $REDIS_HOST 6379; do
  echo "Waiting..."
  sleep 0.5 # wait for half a second before checking again
done

# Migrate the database and seed values for new dev databases
echo "Performing database migration"
pipenv run ./manage.py migrate
if [[ $DJANGO_DEBUG != "False" && EMPTY_DB -eq 1 ]]; then
  echo "Seeding DB with data"
  pipenv run ./manage.py loaddata db_seed.json
fi

if [[ -z $DJANGO_SUPERUSER_EMAIL ]]; then
  echo "Missing variable DJANGO_SUPERUSER_EMAIL to set superuser"
elif [[ $(pipenv run ./manage.py createsuperuser --no-input >/dev/null 2>&1) -eq 0 ]]; then
  echo "Created superuser $DJANGO_SUPERUSER_EMAIL"
else
  echo "Superuser $DJANGO_SUPERUSER_EMAIL already exists"
fi

if [[ -z $1 ]]; then
  echo "Starting Celery processes"
  pipenv run celery -A core worker -l info &

  # Start the app server, either for the dev or prod environment
  if [[ $DJANGO_DEBUG != "False" ]]; then
    echo "Starting Django dev server"
    pipenv run ./manage.py runserver "$DAPHNE_HOST:$CORE_DEV_SERVER_PORT"
  else
    echo "Starting Daphne"
    pipenv run daphne core.asgi:application \
        --bind "$DAPHNE_HOST" \
        --port "8000"
  fi
elif [[ $1 == "test" ]]; then
  echo "Starting Django test runner"
  pipenv run ./manage.py "${@:1}"
elif [[ $1 == "coverage" ]]; then
  echo "Starting test coverage analysis"
  pipenv run coverage run --source='.' manage.py test
  pipenv run coverage html
  DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
  echo "Coverage analysis created: file:$DIR/htmlcov/index.html"
elif [[ $1 == "pytest" ]]; then
  pytest
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
