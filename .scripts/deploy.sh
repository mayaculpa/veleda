#!/bin/bash

# exit with nonzero exit code if anything fails
set -e

if [ $TRAVIS_BRANCH != 'production' ] ; then
    echo "Pushing to staging"
    export REMOTE=staging.veleda.io
else
    echo "Pushing to production"
    export REMOTE=veleda.io
fi

git remote add deploy "deploy@$REMOTE:/home/deploy/repo/"
git push -f deploy $TRAVIS_BRANCH

ssh -t deploy@"$REMOTE" "\
    mkdir -p veleda &&
    git --work-tree=./veleda --git-dir=./repo checkout -f $TRAVIS_BRANCH &&
    cd veleda &&
    ./start.sh"
