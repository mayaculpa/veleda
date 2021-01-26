#!/bin/bash

set -e

# As of git 2.22 use 'git branch --show-current'
export BRANCH="$(git rev-parse --abbrev-ref HEAD)"
export REMOTE_URL="openfarming.ai"
export REPO_NAME="sdg-server"

echo "Reseting production remote"
git remote remove production || true
git remote add production "deploy@$REMOTE_URL:/home/deploy/repo"

echo "Pushing $BRANCH branch to $REMOTE_URL"
git push -f production $BRANCH

ssh -t "deploy@$REMOTE_URL" "\
    mkdir -p $REPO_NAME &&
    git --work-tree=./$REPO_NAME --git-dir=./repo checkout -f $BRANCH &&
    cd $REPO_NAME &&
    ./start.sh"
