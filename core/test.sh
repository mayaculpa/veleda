#!/bin/bash

# Exit with nonzero exit code if anything fails
set -e

# Move the working directory to get the correct Pipenv environment 
cd "$(dirname "$0")"

# Run the tests
pipenv run ./manage.py test

# Run the coverage
pipenv run coverage run manage.py test

# Publish test coverage
if [ "$CONTINUOUS_INTEGRATION" = true ]; then
    codecov
else
    echo "Publishing coverage report in $PWD/htmlcov/index.html"
    pipenv run coverage html
fi
