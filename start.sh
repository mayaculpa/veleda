#!/bin/bash

# exit with nonzero exit code if anything fails
set -e

bold=$(tput bold)
normal=$(tput sgr0)

# Prefix 'sdg-server' has to match the parent deploy folder on the server.
echo "${bold}sdg-server: Creating data volumes${normal}"
docker volume create sdg-server_jekyll-data

echo "${bold}sdg-server: Building Jekyll site${normal}"
docker run --rm \
  --volume="$PWD/jekyll:/srv/jekyll" \
  --volume="jekyll-cache:/usr/local/bundle" \
  -it jekyll/jekyll:latest \
  jekyll build

echo "${bold}sdg-server: Copying site to jekyll-data volume${normal}"
docker run \
  --name helper \
  --volume="sdg-server_jekyll-data:/web" \
  -it busybox \
  true
docker cp jekyll/web/. helper:/web
docker rm helper

echo "${bold}sdg-server: Building stack${normal}"
docker-compose build

echo "${bold}sdg-server: Starting stack${normal}"
docker-compose up -d
