#!/bin/bash

# exit with nonzero exit code if anything fails
set -e

bold=$(tput bold)
normal=$(tput sgr0)

# Use the first parameter to check which environment to use
if [[ $1 == "production" ]]; then
  DOCKER_COMPOSE_FILES=("-f" "production.yml" "-f" "production-volumes.yml")
  export DEPLOY_TYPE="production"
  if [[ ! -f "secrets.docker" ]]; then
    echo "Please configure secrets.docker from secrets.docker.example template"
    exit 1
  fi
  set -a;
  source secrets.docker
  set +a
elif [[ $1 == "staging" ]]; then
  DOCKER_COMPOSE_FILES=("-f" "production.yml" "-f" "staging-volumes.yml")
  export DEPLOY_TYPE="staging"
elif [[ $1 == "development" ]]; then
  echo "Currently not functional. Please use core/start.sh"
  exit 1
  DOCKER_COMPOSE_FILES="-f development.yml"
  export DEPLOY_TYPE="development"
else
  echo "Please start as $0 production or $0 development"
  exit 1
fi

# Source the CORE_DOMAIN  and MINIO_DOMAIN value for Traefik in the Docker Compose file
eval $(source "core/secrets.core"; echo CORE_DOMAIN="$CORE_DOMAIN";)
export CORE_DOMAIN="$CORE_DOMAIN"
eval $(source "minio/secrets.minio"; echo MINIO_DOMAIN="$MINIO_DOMAIN";)
export MINIO_DOMAIN="$MINIO_DOMAIN"

# If there is no second parameter, start the stack, else use all remaining
# positional parameters after the docker-compose command.
#  - Starts the staging stack: ./start.sh staging
#  - Shows running production processes: ./start.sh production ps
#  - Shows the logs of the core service: ./start.sh production logs core
echo "Using with ${bold}$1${normal} configuration"
if [[ -z ${2+x} ]]; then
  echo "sdg-server: Building stack"
  docker-compose ${DOCKER_COMPOSE_FILES[@]} build

  echo "sdg-server: Starting stack"
  docker-compose ${DOCKER_COMPOSE_FILES[@]} up -d
else
  shift
  docker-compose ${DOCKER_COMPOSE_FILES[@]} "$@"
fi

