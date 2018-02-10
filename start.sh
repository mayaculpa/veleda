bold=$(tput bold)
normal=$(tput sgr0)

echo "${bold}veleda: Building Jekyll site${normal}"
docker run --rm \
  --volume="$PWD/jekyll:/srv/jekyll" \
  --volume="veledaio_jekyll-cache:/usr/local/bundle" \
  -it jekyll/jekyll:latest \
  jekyll build

echo "${bold}veleda: Copying site to jekyll-data volume${normal}"
docker run \
  --name helper \
  --volume="veledaio_jekyll-data:/web" \
  -it busybox \
  true
docker cp jekyll/web/. helper:/web
docker rm helper

echo "${bold}veleda: Building stack${normal}"
docker-compose build

echo "${bold}veleda: Starting stack${normal}"
docker-compose up -d
