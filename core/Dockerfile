FROM python:3.5.2
MAINTAINER Moritz Ulmer <moritz.ulmer@posteo.de>

# Install packages
RUN apt-get update && apt-get install -y \
        netcat-openbsd

# Create the group and user to be used in this container
RUN groupadd flaskgroup && useradd -m -g flaskgroup -s /bin/bash flask

# Create the working directory (and set it as the working directory)
RUN mkdir -p /home/flask/app/web
WORKDIR /home/flask/app/web

# Install the package dependencies (this step is separated
# from copying all the source code to avoid having to
# re-install all python packages defined in requirements.txt
# whenever any source code change is made)
COPY requirements.txt /home/flask/app/web
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY . /home/flask/app/web

RUN chown -R flask:flaskgroup /home/flask

USER flask
