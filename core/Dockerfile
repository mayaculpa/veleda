FROM python:3.7.3
MAINTAINER Moritz Ulmer <moritz.ulmer@posteo.de>

# Install Python and Package Libraries
RUN apt-get update && apt-get upgrade -y && apt-get autoremove && apt-get autoclean
RUN apt-get install -y \
    netcat-openbsd \
    vim

# Project Files and Settings
ARG PROJECT=core
ARG PROJECT_DIR=/var/www/${PROJECT}

# Install the dependencies
RUN mkdir -p $PROJECT_DIR
WORKDIR $PROJECT_DIR
COPY Pipfile Pipfile.lock ./
RUN pip install -U pipenv
RUN pipenv install --system

# Copy the source files
COPY ./ ./

# Server
EXPOSE 8000
STOPSIGNAL SIGINT
ENTRYPOINT ["bash"]
CMD ["./start.sh"]
