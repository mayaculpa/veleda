bold=$(tput bold)
normal=$(tput sgr0)

# Prefix 'flowleafserver' has to match the parent deploy folder on the server. Hyphens are removed from filenames
echo "${bold}flow-leaf-server: Creating data volumes${normal}"
docker volume create flowleafserver_influxdb-data
docker volume create flowleafserver_grafana-data
docker volume create flowleafserver_postgres-data
docker volume create flowleafserver_jekyll-data

echo "${bold}flow-leaf-server: Building Jekyll site${normal}"
docker run --rm \
  --volume="$PWD/jekyll:/srv/jekyll" \
  --volume="jekyll-cache:/usr/local/bundle" \
  -it jekyll/jekyll:latest \
  jekyll build

echo "${bold}flow-leaf-server: Copying site to jekyll-data volume${normal}"
docker run \
  --name helper \
  --volume="flowleafserver_jekyll-data:/web" \
  -it busybox \
  true
docker cp jekyll/web/. helper:/web
docker rm helper

echo "${bold}flow-leaf-server: Building stack${normal}"
docker-compose build

echo "${bold}flow-leaf-server: Starting stack${normal}"
docker-compose up -d
