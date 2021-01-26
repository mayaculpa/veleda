#!/bin/bash

# Exit with nonzero exit code if anything fails
set -e
# Ensure the script is running in this directory
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

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
