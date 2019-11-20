FROM python:3.7.5
LABEL maintainer="moritz.ulmer@posteo.de"

# Install Python and Package Libraries
RUN apt-get update && apt-get upgrade -y && apt-get autoremove && apt-get autoclean
RUN apt-get install -y \
    netcat-openbsd \
    vim

# Project Files and Settings
ARG USERNAME=core
ARG PROJECT_DIR=/home/$USERNAME/
RUN groupadd -r $USERNAME && useradd --no-log-init -r -g $USERNAME $USERNAME
RUN mkdir -p $PROJECT_DIR && chown $USERNAME:$USERNAME $PROJECT_DIR
WORKDIR $PROJECT_DIR
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

# Drop user privileges
USER $USERNAME

# Install the dependencies
COPY Pipfile Pipfile.lock ./
RUN pip install --user pipenv && pipenv install

# Copy the source files
COPY ./ ./
RUN pipenv run ./manage.py collectstatic

# Server
EXPOSE 8000
STOPSIGNAL SIGINT
ENTRYPOINT ["bash"]
CMD ["./start.sh"]
