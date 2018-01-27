[![Build Status](https://travis-ci.org/mayaculpa/veleda.svg?branch=master)](https://travis-ci.org/mayaculpa/veleda)

# Veleda

## Docker Compose

Start the complete setup with:

    docker-compose build && docker-compose up -d

Stop the setup with:

    docker-compose down

Key data to the individual services:

| Name     | Purpose              | Port | Documentation |
| -------- | -------------------- | ---- |---------------|
| web      | User management      | 8001 | [readme](web/README.md) |
| postgres | User storage         | 5431 |  |
| redis    | Async task storage   | 6379 |  |
| influxdb | Time series storage  | 8086 |  |
| grafana  | Time series analysis | 3000 | [readme](grafana/README.md) |
