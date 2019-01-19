#!/bin/bash

REPO_NAME=flow-leaf-server
BASE_URL=flowleaf.co

# exit with nonzero exit code if anything fails
set -e

# Only deploy merge request builds
if [[ $TRAVIS_PULL_REQUEST == "false" ]]; then
  echo "Aborting deploy as not a pull request"
  exit 0;
fi

# Add the SSH login key
chmod 600 flowleaf-deploy-key
mv flowleaf-deploy-key ~/.ssh/id_rsa

# Register the FlowLeaf staging and production server SSH keys
echo '|1|v2IIOykLxZAuYvftBc3fyoZKQMY=|pYT/ExmN20Z9rkIyFSoo+NBm4lY= ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC1k/w9ySC0cic8PnrxXxW3ceo/Mm9Euja8NyHtQggjFXbZY0GH9pY155BozKOTq5WaeuTBzU5QsLsVLUAxrEKXwsie4AxiCYqlChxNaVxxQMEyBcuqcy3AMocDudNEGz9hOWfEU6VMMf6HHiZsExqBy1s5pEfxmfQvOOkRmcHRmv1KSuQ0+TOqPXRn49BwjGYff0URhHn1rFlcEDAvGjamwXqMNm0ACjYK8JcEAFzSkWHazL/nw9q7ZPWFAVQIMUAeh3d3/79HuVae9T3IIVRccpEbMnUK4M9sc48SaJXUxvylWXPIkJ7Xjc7ibsEWxQt/kUxOVtvs9YhGwdmec1ID' >> $HOME/.ssh/known_hosts
echo '|1|iu4b5h1OW+OpP8M796mUJFoVEhI=|fwUJjq4g4CBx3zqjf6k0sprcTKI= ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC4zVUlbnMAdLLwfhlbnSRcFXwr08iFdov/xNAaP6ErBFdPjZVUOpUgC8MVuEotgRgi3QbggSJqhhD5v965bIECi8KfYX8socrNCMOb7lNuW/BwkkKQykbyvzSLxYgixqjgDgNl6jsRAcqOIiTFcifu/oEL8GFO5/Fu10AMMFsQzGWsq9pV/SBHn2uehqNXNjltj7RNpd0XSmCzX7zQYS2e+3eSwRp6HupzOvIXvJpyXG8fz5jJRHXHXu3Z471djO7S+NEKzfNobLV0d7atBSr7jVdOv5g9whrqfoygFLrvKZe4CRx2QM1pwlYT2ZZV3huKOmoJ577HP3uv2C+KY1Bz' >> $HOME/.ssh/known_hosts

# Select the remote to push to depending on the branch
if [ $TRAVIS_BRANCH != 'production' ] ; then
    echo "Pushing to staging: Merge of $TRAVIS_PULL_REQUEST_BRANCH into $TRAVIS_BRANCH"
    export REMOTE="staging.$BASE_URL"
else
    echo "Pushing to production: Merge of $TRAVIS_PULL_REQUEST_BRANCH into $TRAVIS_BRANCH"
    export REMOTE="$BASE_URL"
fi

# Push to the remote server
git remote add deploy "deploy@$REMOTE:/home/deploy/repo/"

# Required when deploying a feature branch
#if ! $(git show-ref -q --heads $TRAVIS_PULL_REQUEST_BRANCH); then
#  echo "Creating new branch $TRAVIS_PULL_REQUEST_BRANCH" 
#  git checkout -b $TRAVIS_PULL_REQUEST_BRANCH
#fi

echo "Pushing branch to server"
git push -f deploy $TRAVIS_BRANCH

# Unpack and update the Docker services
ssh -t deploy@"$REMOTE" "\
    mkdir -p $REPO_NAME &&
    git --work-tree=./$REPO_NAME --git-dir=./repo checkout -f $TRAVIS_BRANCH &&
    cd $REPO_NAME &&
    ./start.sh"

