#!/bin/bash

# exit with nonzero exit code if anything fails
set -e

# Install Python dependencies
pip install -r core/requirements-test.txt

# Copy settings into secrets.core file
cp core/secrets.core.example core/secrets.core
echo 'INTEGRATION_TESTS=True' >> core/secrets.core
echo 'FLASK_CONFIG=production' >> core/secrets.core

# Set up default configuration settings
while IFS= read -r var
do
  cp "$var"".example" "$var"
done < './.scripts/configuration-files.txt'
