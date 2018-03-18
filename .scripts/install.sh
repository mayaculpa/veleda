#!/bin/bash

# exit with nonzero exit code if anything fails
set -e

# Install Python dependencies
pip install -r core/requirements-test.txt
