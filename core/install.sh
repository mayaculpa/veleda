#!/bin/bash

# Exit with nonzero exit code if anything fails
set -e
# Ensure the script is running in this directory
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

# Install package requirements
requiredAptPackages="python3-pip libpq-dev postgresql-client-12"
echo "Installing system packages: $requiredAptPackages"
sudo apt install python3-pip libpq-dev postgresql-client-12

# Install Pipenv and Python packages. The CI has no user profile.
# Do not install the dev packages in production
echo "Installing Python packages"
if [[ "$CI" == true ]]; then
  python3 -m pip install pipenv
else
  python3 -m pip install --user pipenv
fi
if [[ $DJANGO_DEBUG != "False" ]]; then
  pipenv install --dev
else
  pipenv install
fi

# Copy default secret files
echo "Checking secret files and copying from defaults if missing"
secretFiles=("./secrets.core" "./secrets.rabbitmq" "../postgres/secrets.postgres" "../redis/secrets.redis")
for secretFile in ${secretFiles[@]}; do
  if [[ -f $secretFile ]]; then
    echo "Found $secretFile"
  else
    echo "Copying default from $secretFile.example to $secretFile"
    cp "$secretFile.example" "$secretFile"
  fi
done

# Collect static files
echo "Collecting static files. "
pipenv run ./manage.py collectstatic --noinput
