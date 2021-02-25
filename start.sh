#!/bin/bash

# exit with nonzero exit code if anything fails
set -e

bold=$(tput bold)
normal=$(tput sgr0)

# Use the first parameter to check which environment to use
if [[ $1 == "production" ]]; then
  DOCKER_COMPOSE_FILE="production.yml"
  export DEPLOY_TYPE="production"
elif [[ $1 == "staging" ]]; then
  DOCKER_COMPOSE_FILE="production.yml"
  export DEPLOY_TYPE="staging"
elif [[ $1 == "development" ]]; then
  DOCKER_COMPOSE_FILE="development.yml"
  export DEPLOY_TYPE="development"
else
  echo "Please start as $0 production or $0 development"
  exit 1
fi

# Source the CORE_DOMAIN value for Traefik in the Docker Compose file
eval $(source "core/secrets.core"; echo CORE_DOMAIN="$CORE_DOMAIN";)
export CORE_DOMAIN="$CORE_DOMAIN"

# If there is no second parameter, start the stack, else use all remaining
# positional parameters after the docker-compose command.
#  - Starts the staging stack: ./start.sh staging
#  - Shows running production processes: ./start.sh production ps
#  - Shows the logs of the core service: ./start.sh production logs core
echo "Using with ${bold}$1${normal} configuration"
if [[ -z ${2+x} ]]; then
  echo "sdg-server: Building stack"
  docker-compose -f "$DOCKER_COMPOSE_FILE" build

  echo "sdg-server: Starting stack"
  docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
else
  shift
  docker-compose -f "$DOCKER_COMPOSE_FILE" "$@"
fi

