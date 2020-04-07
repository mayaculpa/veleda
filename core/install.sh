#!/bin/bash

# exit with nonzero exit code if anything fails
set -e

# Install Pipenv
python3 -m pip install pipenv

# Install Python dependencies
cd "$(dirname "$0")"
pipenv sync -d

# Collect all static files
pipenv run ./manage.py collectstatic
