# PostgreSQL Database

To connect to a Docker instance of the database use:

    psql -p 5431 -h localhost -U web_user -W web_db

When using a local PostgreSQL instance use, after having set up your user role:

    psql web_db
