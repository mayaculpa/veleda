#!/bin/bash

REPO_NAME=flow-leaf-server
BASE_URL=flowleaf.co

# exit with nonzero exit code if anything fails
set -e

# Add the SSH login key
chmod 600 flowleaf-deploy-key
mv flowleaf-deploy-key ~/.ssh/id_rsa

# Register the FlowLeaf staging and production server SSH keys
echo '|1|BqdQKtUnA/AtCT/p2M7wgMq3wlY=|lH39cRtAE64wd6EG3ry2J9ewXic= ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBH3antqwy3D4NVVfHQX3SQc/g4wl/SAVC9w9QEry7hhQmB0SJIprwNAq8Hy2DzVCS7kTj/q7fCiiL7oAznrax+0=' >> $HOME/.ssh/known_hosts
echo '|1|+Z7oOsZ+zdL6u8o8VSWp+bRzd2g=|XMw2HyJIHoekOYlJYw1n75plL2E= ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBCJ/fa/mr577/qCuRXqUNccfmhpUtmi46LSyE7nDbOgxv8kZFs7yQ/sh6TM5npR+ZIbe9I0qmdvA+cE1QfvN21E=' >> $HOME/.ssh/known_hosts

# Select the remote to push to depending on the branch
if [ $TRAVIS_BRANCH != 'production' ] ; then
    echo "Pushing to staging"
    export REMOTE="staging.$BASE_URL"
else
    echo "Pushing to production"
    export REMOTE="$BASE_URL"
fi

# Push to the remote server
git remote add deploy "deploy@$REMOTE:/home/deploy/repo/"
git push -f deploy $TRAVIS_BRANCH

# Unpack and update the Docker services
ssh -t deploy@"$REMOTE" "\
    mkdir -p $REPO_NAME &&
    git --work-tree=./$REPO_NAME --git-dir=./repo checkout -f $TRAVIS_BRANCH &&
    cd $REPO_NAME &&
    ./start.sh"
