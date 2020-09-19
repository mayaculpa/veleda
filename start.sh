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

echo "Starting with ${bold}$1${normal} configuration"
echo "sdg-server: Building stack"
docker-compose -f "$DOCKER_COMPOSE_FILE" build

echo "sdg-server: Starting stack"
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
