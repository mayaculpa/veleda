#!/bin/bash

# exit with nonzero exit code if anything fails
set -e

# Install Pipenv
pip install pipenv

# Install Python dependencies
cd "$(dirname "$0")"
pipenv sync -d

# Collect all static files
pipenv run ./manage.py collectstatic
