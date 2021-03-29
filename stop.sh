#!/bin/bash

# exit with nonzero exit code if anything fails
set -e

./start.sh $@ stop
