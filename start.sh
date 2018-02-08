bold=$(tput bold)
normal=$(tput sgr0)

echo "${bold}veleda: Building Jekyll site${normal}"
docker run --rm \
  --volume="$PWD/jekyll:/srv/jekyll" \
  --volume="jekyll-cache:/usr/local/bundle" \
  -it jekyll/jekyll:latest \
  jekyll build

echo "${bold}veleda: Building stack${normal}"
docker-compose build

echo "${bold}veleda: Starting stack${normal}"
docker-compose up -d
