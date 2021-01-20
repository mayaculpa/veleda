# Troubleshooting Core Service

## Install script fails due to "--user"

When the install script runs `python3 -m pip install --user pipenv` and it is currently in a virutalenv, it is not able to access the user directory. Please create a new terminal which has the system Python packages loaded.