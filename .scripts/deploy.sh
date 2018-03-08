#!/bin/bash
if [ $TRAVIS_BRANCH != 'master' ] ; then
    echo "Pushing to staging"
    git remote add deploy "deploy@staging.veleda.io:/home/deploy/veleda/"
else
    echo "Pushing to production"
    git remote add deploy "deploy@veleda.io:/home/deploy/veleda/"
fi

git push -f deploy $TRAVIS_BRANCH

ssh deploy@staging.veleda.io 'bash -s' < \
    "cd veleda && \
     git checkout -f $TRAVIS_BRANCH && \
     ./start.sh"
