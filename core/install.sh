#!/bin/bash

# exit with nonzero exit code if anything fails
set -e

# Install package requirements
requiredAptPackages="python3-pip libpq-dev postgresql-client-12"
echo "Installing system packages: $requiredAptPackages"
sudo apt install python3-pip libpq-dev postgresql-client-12

# Install Pipenv and Python packages
echo "Installing Python packages"
python3 -m pip install --user pipenv
pipenv install

# Copy default secret files
echo "Checking secret files and copying from defaults if missing"
secretFiles=("./secrets.core" "./secrets.rabbitmq" "../postgres/secrets.postgres" "../redis/secrets.redis")
for secretFile in ${secretFiles[@]}; do
  if [ -f $secretFile ]; then
    echo "Found $secretFile"
  else
    echo "Copying default from $secretFile.example to $secretFile"
    cp "$secretFile.example" "$secretFile"
  fi
done

# Collect static files
echo "Collecting static files"
pipenv run ./manage.py collectstatic
