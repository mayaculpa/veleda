FROM postgres:10
LABEL maintainer="moritz.ulmer@posteo.de"

# Create the default user (core_user) and DB (core_db). Will only be executed
# if no previous volume exists
COPY web-init.sql /docker-entrypoint-initdb.d/10-web-init.sql
