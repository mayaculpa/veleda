#!/bin/bash

# exit with nonzero exit code if anything fails
set -e

bold=$(tput bold)
normal=$(tput sgr0)

if [[ $1 == "production" ]]; then
  DOCKER_COMPOSE_FILE="production.yml"
elif [[ $1 == "development" ]]; then
  DOCKER_COMPOSE_FILE="development.yml"
else
  echo "Please start as $0 production or $0 development"
  exit 1
fi

echo "Stopping ${bold}$1${normal} stack"
docker-compose -f "$DOCKER_COMPOSE_FILE" stop