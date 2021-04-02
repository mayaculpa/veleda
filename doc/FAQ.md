# Frequently Asked Questions

## User Focused

## Developer Focused

### The core component is returning "Internal Server Error"

#### Problem

1. If started with Docker Compose or the top-level `start.sh` script (not `core/start.sh`)
2. Check the logs with `docker logs core`
2. If a Redis "Connection closed by server." related error occurs, check whether in `core/secrets.core`, `FLASK_CONFIG` is set and that it is set to `production`

#### Solution

1. Stop all containers with `docker-compose down`
2. Define `FLASK_CONFIG=production` in `core/secrets.core`
2. Start the containers with the top-level `./start.sh`
