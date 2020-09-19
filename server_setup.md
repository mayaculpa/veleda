# Server Setup

## Installation
- Create an Ubuntu 18.04 server
- Install Docker
  - `sudo apt-get update`
  - `sudo apt-get install apt-transport-https ca-certificates curl software-properties-common`
  - `curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -`
  - `sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"`
  - `sudo apt-get update`
  - `sudo apt-get install docker-ce`
- Install Docker Compose
  - ``curl -L https://github.com/docker/compose/releases/download/1.19.0/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose``
  - `chmod +x /usr/local/bin/docker-compose`
- Add *deploy* user
  - `adduser deploy`
- Add SSH access for *deploy*
  - `mkdir /home/deploy/.ssh`
  - `cp .ssh/authorized_keys /home/deploy/.ssh`
  - `chown deploy:deploy -R /home/deploy/.ssh`
- Add *deploy* to *docker* group
  - `usermod -aG docker deploy`

## Environment Setup

- Login as *deploy*
- Generate private secrets
  - Files where they have to be set
  - `grafana/secrets.grafana`
  - `influxdb/secrets.influxdb`
  - `postgres/secrets.postgres`
  - `postgres/web-init.sql`
  - `core/secrets.core`
- Set server name
  - Set the server names in the `production.yml` file for the service labels which are used by the Traefik reverse proxy
    - core
    - grafana
    - planner
  - Set the OAuth URLs in `grafana/secrets.grafana`
    - Replace *localhost:3000* with the grafana domain name (data.example.com)
    - Replace *localhost:8000* with the core domain name (core.example.com)
- Configure Traefik as the reverse proxy and TLS termination endpoint

## Local Setup

To enable browsing of the services on a local machine, use localhost and the appropriate port.

## Optional:

Update the deploy process:
- Set up the server to be deployed to
  - `mkdir repo && cd repo`
  - `git init --bare`
- Update the deploy script
  - Update the *REMOTE* definition in `.scripts/deploy.sh` 

## Start
- `./start.sh production`
