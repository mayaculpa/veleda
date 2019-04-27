#!/bin/bash

# exit with nonzero exit code if anything fails
set -e

# Run tests and coverage of each component
core/test.sh
