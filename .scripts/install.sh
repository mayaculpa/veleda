#!/bin/bash

# exit with nonzero exit code if anything fails
set -e

# Configure SSH deploy setup
chmod 600 veleda-deploy-key
mv veleda-deploy-key ~/.ssh/id_rsa
echo '|1|BqdQKtUnA/AtCT/p2M7wgMq3wlY=|lH39cRtAE64wd6EG3ry2J9ewXic= ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBH3antqwy3D4NVVfHQX3SQc/g4wl/SAVC9w9QEry7hhQmB0SJIprwNAq8Hy2DzVCS7kTj/q7fCiiL7oAznrax+0=' >> $HOME/.ssh/known_hosts
echo '|1|+Z7oOsZ+zdL6u8o8VSWp+bRzd2g=|XMw2HyJIHoekOYlJYw1n75plL2E= ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBCJ/fa/mr577/qCuRXqUNccfmhpUtmi46LSyE7nDbOgxv8kZFs7yQ/sh6TM5npR+ZIbe9I0qmdvA+cE1QfvN21E=' >> $HOME/.ssh/known_hosts

# Install Python dependencies
pip install -r core/requirements-test.txt
