#!/bin/bash

# exit with nonzero exit code if anything fails
set -e

# Install NPM dependencies
cd "$(dirname "$0")"
npm ci
