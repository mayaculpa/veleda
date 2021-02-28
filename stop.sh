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

# Stop all running processes for the specified environment
echo "Stopping ${bold}$1${normal} stack"
docker-compose -f "$DOCKER_COMPOSE_FILE" stop

