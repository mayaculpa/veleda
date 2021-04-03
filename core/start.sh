#!/bin/bash

function finish {
  # Kills all forked processes (Celery worker)
  pkill -P $$ || true
}
trap finish EXIT

# Exit with nonzero exit code if anything fails
set -e
# Ensure the script is running in this directory
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

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
  source ../minio/env.minio
  source ../minio/secrets.minio
  DJANGO_DEBUG=True
  
  echo "Updating the service hostnames to localhost"
  export DATABASE_HOST="127.0.0.1"
  export RABBITMQ_HOST="127.0.0.1"
  unset RABBITMQ_DEFAULT_USER
  unset RABBITMQ_DEFAULT_PASS
  export DAPHNE_HOST="$CORE_DOMAIN"
  export REDIS_HOST="127.0.0.1"
  export MINIO_HOST="127.0.0.1"
  
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
      -p $REDIS_HOST:$REDIS_PORT:$REDIS_PORT \
      -d \
      redis:5 \
      "redis-server" "--requirepass" "$REDIS_PASSWORD"
  else
    echo "Redis docker service already running"
  fi
  if [[ ! "$(docker ps -a | grep sdg-server-dev-minio)" ]]; then
    echo "Starting MinIO docker service"
    docker run \
      --rm \
      --name sdg-server-dev-minio \
      -p 9000:9000 \
      -e "MINIO_ROOT_USER=$MINIO_ROOT_USER" \
      -e "MINIO_ROOT_PASSWORD=$MINIO_ROOT_PASSWORD" \
      -d \
      minio/minio:RELEASE.2021-03-26T00-00-41Z \
      "server" "/data"
  else
    echo "MinIO docker service already running"
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
  if [[ "$(docker ps -a | grep sdg-server-dev-minio)" ]]; then
    docker stop sdg-server-dev-minio
  else
    echo "MinIO storage already stopped"
  fi
}

get_minio_client() {
  if [[ ! -f "mc" ]]; then
    wget https://dl.min.io/client/mc/release/linux-amd64/mc
    chmod +x mc
  fi
}

if [[ $1 == "help" ]]; then
  print_help
  exit 0
fi

if [[ $DJANGO_DEBUG != "False" ]]; then
  if [[ $DJANGO_ENV_LOADED != True ]]; then
    if [[ $1 == "clean" ]]; then
      stop_docker_services
      set +e
      exit 0
    else
      echo "Starting in debug mode"
      source_debug_env_variables
      start_docker_services
      get_minio_client
    fi
  else
    echo "Starting in docker debug mode"
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
while ! nc -z $REDIS_HOST $REDIS_PORT; do
  echo "Waiting..."
  sleep 0.5 # wait for half a second before checking again
done

echo "Waiting for MinIO to launch on 9000..."
while ! nc -z $MINIO_HOST $MINIO_PORT; do
  echo "Waiting..."
  sleep 0.5 # wait for half a second before checking again
done

# Add the MinIO server URL
./mc alias set core-s3-server \
  "http://$MINIO_HOST:$MINIO_PORT" \
  "$MINIO_ROOT_USER" \
  "$MINIO_ROOT_PASSWORD"
# If the user does not exist add them and the respective policy
if ! ./mc admin user list core-s3-server | grep -q "$MINIO_ACCESS_KEY_ID"; then
  echo "Adding user $MINIO_ACCESS_KEY_ID and bucket policy to MinIO server"
  ./mc admin user add core-s3-server "$MINIO_ACCESS_KEY_ID" "$MINIO_SECRET_ACCESS_KEY"
  ./mc mb "core-s3-server/$MINIO_STORAGE_BUCKET_NAME"
  cat > "s3-policy.json" << EOL
   {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ListObjectsInBucket",
            "Effect": "Allow",
            "Action": ["s3:ListBucket"],
            "Resource": ["arn:aws:s3:::${MINIO_STORAGE_BUCKET_NAME}"]
        },
        {
            "Sid": "AllObjectActions",
            "Effect": "Allow",
            "Action": "s3:*Object",
            "Resource": ["arn:aws:s3:::${MINIO_STORAGE_BUCKET_NAME}/*"]
        }
    ]
  }
EOL
  ./mc admin policy add core-s3-server "readwrite-$MINIO_STORAGE_BUCKET_NAME" "s3-policy.json"
  rm "s3-policy.json"
  ./mc admin policy set core-s3-server "readwrite-$MINIO_STORAGE_BUCKET_NAME" "user=$MINIO_ACCESS_KEY_ID"
else
  echo "MinIO user $MINIO_ACCESS_KEY_ID already exists"
fi

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
  if [ "$CONTINUOUS_INTEGRATION" == true ]; then
    pipenv run codecov || true
  else
    pipenv run coverage html
    DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
    echo "Coverage analysis created: file:$DIR/htmlcov/index.html"
  fi
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
