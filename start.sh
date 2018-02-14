bold=$(tput bold)
normal=$(tput sgr0)

echo "${bold}veleda: Creating data volumes${normal}"
docker volume create influxdb-data
docker volume create grafana-data
docker volume create postgres-data
docker volume create jekyll-data

echo "${bold}veleda: Building Jekyll site${normal}"
docker run --rm \
  --volume="$PWD/jekyll:/srv/jekyll" \
  --volume="jekyll-cache:/usr/local/bundle" \
  -it jekyll/jekyll:latest \
  jekyll build

echo "${bold}veleda: Copying site to jekyll-data volume${normal}"
docker run \
  --name helper \
  --volume="jekyll-data:/web" \
  -it busybox \
  true
docker cp jekyll/web/. helper:/web
docker rm helper

echo "${bold}veleda: Building stack${normal}"
docker-compose build

echo "${bold}veleda: Starting stack${normal}"
docker-compose up -d
