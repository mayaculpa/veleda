#!/bin/bash

# Exit with nonzero exit code if anything fails
set -e

# Move the working directory to get the correct npm environment 
cd "$(dirname "$0")"

# Run all test types
npm run lint
npm run test -- --no-watch --browsers=ChromeHeadless
npm run e2e

# Publish the test results
npx codecov
