#!/bin/bash

REPO_NAME="sdg-server"
BASE_URL="openfarming.ai"
GIT_REMOTE="staging"

# exit with nonzero exit code if anything fails
set -e

echo '$TRAVIS_BRANCH' = "$TRAVIS_BRANCH"
echo '> git branch'
git branch
echo ''
echo '> git diff master --stat'
git diff master --stat
echo ''

# Add the SSH login key
chmod 600 ~/.ssh/sdg-staging-deploy-key

# Register the SDG staging server SSH key
echo '|1|Dei180U2g2nwmokSrOKPWMJf600=|BrLInQgYNC/5AbAp5Q/TrS6LXmM= ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDCnPKHvz9IPWWqYHmjF6is6s9u75+54xYmfz9nHVPpmb2Oq7gmJzUqsIqji7LOSj9VmkO3HFT5K77J/VhWJiW69/3XGrv0Bj5BTzxodDkZKn4aMt21y/ng0+ZhIdWJonfyONhRddCTaNiI9udu785IjxKMuCqgmT1HRYbIWzBtc45U6WiNHWljGPVmW3y5ScdpVQ77Rkg3jmvrx6/+REEkpJwdpmX1PrjJVhjsJlMxiwW40Hg/98YPCYG5R03HqU8VMP1upXquSFA3pB9cKwbUept34gAJSiqbyDIuD/hLrgv32+At5Ofwzd/Uuj+dGqaqwxz9ckbeef1CU0Qn2mbL' >> $HOME/.ssh/known_hosts

# Push only if the master is the target branch
if [ $TRAVIS_BRANCH == 'master' ] ; then
    echo "Pushing "$TRAVIS_BRANCH" to staging"
    export REMOTE="staging.$BASE_URL"
    export TARGET_BRANCH="deploy-branch"
    # Recreate the feature branch as Travis is on HEAD
    git checkout -b "$TARGET_BRANCH"
else
    echo "Not deploying the $TRAVIS_BRANCH to staging. Has to be the master branch. Exiting."
    exit 1
fi

# Push to the remote server
git show
git remote add "$GIT_REMOTE" "deploy@$REMOTE:/home/deploy/repo/"

echo "Pushing $TARGET_BRANCH branch to server"
git push -f "$GIT_REMOTE" "$TARGET_BRANCH"

# Unpack and update the Docker services
ssh -t deploy@"$REMOTE" "\
    mkdir -p $REPO_NAME &&
    git --work-tree=./$REPO_NAME --git-dir=./repo checkout -f $TARGET_BRANCH &&
    cd $REPO_NAME &&
    ./start.sh"

