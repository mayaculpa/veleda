#!/bin/bash

# exit with nonzero exit code if anything fails
set -e

if [ $TRAVIS_BRANCH != 'master' ] ; then
    echo "Pushing to staging"
    git remote add deploy "deploy@staging.veleda.io:/home/deploy/repo/"
else
    echo "Pushing to production"
    git remote add deploy "deploy@veleda.io:/home/deploy/repo/"
fi

git push -f deploy $TRAVIS_BRANCH

ssh -t deploy@staging.veleda.io "mkdir -p veleda &&
    git --work-tree=./veleda --git-dir=./repo checkout -f $TRAVIS_BRANCH &&
    cd veleda &&
    ./start.sh"
