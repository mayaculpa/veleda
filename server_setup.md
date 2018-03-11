# Server Setup

## Installation
- Create an Ubuntu 16.04 server
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

## Veleda Setup
- Login as *deploy*
- Clone the Veleda Git repository
    - `git clone https://github.com/mayaculpa/veleda.git`
    - `cd veleda`
    - `git config receive.denyCurrentBranch updateInstead`
- Setup the secrets
    - Files where they have to be set
    - `grafana/secrets.grafana`
    - `influxdb/secrets.influxdb`
    - `postgres/secrets.postgres`
    - `postgres/web-init.sql`
    - `web/secrets.flask`
- Optional: Set server name
    - Replace *localhost* in `grafana/secrets.grafana`
    - Set the *server_name* in `nginx/nginx.conf`

## Start
- `./start.sh`

