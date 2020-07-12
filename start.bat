echo off

REM Extract script location
SET SCRIPT_PATH=%~dp0
SET SCRIPT_PATH=%SCRIPT_PATH:\=/%
SET SCRIPT_PATH=%SCRIPT_PATH:~0,-1%

REM Prefix 'sdg-server' has to match the parent deploy folder on the server.
echo "sdg-server: Creating data volumes"
docker volume create sdg-server_jekyll-data

echo "sdg-server: Building Jekyll site"
docker run --rm --volume="%SCRIPT_PATH%/jekyll:/srv/jekyll" --volume="jekyll-cache:/usr/local/bundle" -it jekyll/jekyll:latest jekyll build

echo "sdg-server: Copying site to jekyll-data volume"
docker run --name helper --volume="sdg-server_jekyll-data:/web" -it busybox true
docker cp jekyll/web/. helper:/web
docker rm helper

echo "sdg-server: Building stack"
docker-compose build

echo "sdg-server: Starting stack"
docker-compose up -d
