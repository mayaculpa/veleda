#!/bin/bash

# Configure SSH deploy setup
chmod 600 veleda-deploy-key
mv veleda-deploy-key ~/.ssh/id_rsa
echo '|1|BqdQKtUnA/AtCT/p2M7wgMq3wlY=|lH39cRtAE64wd6EG3ry2J9ewXic= ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBH3antqwy3D4NVVfHQX3SQc/g4wl/SAVC9w9QEry7hhQmB0SJIprwNAq8Hy2DzVCS7kTj/q7fCiiL7oAznrax+0=' >> $HOME/.ssh/known_hosts
echo '|1|LkxdfQjwVQsFa00cYoUxhbDn1zQ=|VEhRQMKSUFFKWJDZ6PlrFkTrBBw= ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBOIz4h420Q4iu/xAjTbg4WuZtXa48i9CeDMewWyikj+sMaTA0kQZfZ0toSZPOPocaqkGL7Ec8oNAMBzGthK7/tE=' >> $HOME/.ssh/known_hosts

# Install Python dependencies
pip install -r web/requirements-test.txt
