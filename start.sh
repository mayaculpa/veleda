bold=$(tput bold)
normal=$(tput sgr0)

# Prefix 'flow-leaf-server' has to match the parent deploy folder on the server
echo "${bold}flow-leaf-server: Creating data volumes${normal}"
docker volume create flow-leaf-server_influxdb-data
docker volume create flow-leaf-server_grafana-data
docker volume create flow-leaf-server_postgres-data
docker volume create flow-leaf-server_jekyll-data

echo "${bold}flow-leaf-server: Building Jekyll site${normal}"
docker run --rm \
  --volume="$PWD/jekyll:/srv/jekyll" \
  --volume="jekyll-cache:/usr/local/bundle" \
  -it jekyll/jekyll:latest \
  jekyll build

echo "${bold}flow-leaf-server: Copying site to jekyll-data volume${normal}"
docker run \
  --name helper \
  --volume="flow-leaf-server_jekyll-data:/web" \
  -it busybox \
  true
docker cp jekyll/web/. helper:/web
docker rm helper

echo "${bold}flow-leaf-server: Building stack${normal}"
docker-compose build

echo "${bold}flow-leaf-server: Starting stack${normal}"
docker-compose up -d
