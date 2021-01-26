# Troubleshooting Core Service

## Install script fails due to "--user"

When the install script runs `python3 -m pip install --user pipenv` and it is currently in a virutalenv, it is not able to access the user directory. Please create a new terminal which has the system Python packages loaded.

## In the dev environment, there is no demo data

If an error occured while creating the Docker databases the first time, the database seed might not have been loaded. Clear the data and start the server anew  with the following commands:

    ./start.sh clean
    ./start.sh