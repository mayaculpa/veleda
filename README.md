[![Build Status](https://travis-ci.org/protohaus/sdg-server.svg?branch=main)](https://travis-ci.org/protohaus/sdg-server)
[![codecov](https://codecov.io/gh/protohaus/sdg-server/branch/master/graph/badge.svg)](https://codecov.io/gh/protohaus/sdg-server)

# SmartDigitalGarden / DeviceStacc Server

A data analytics and control platform for IoT systems. It integrates with the [sdg-controller firmware][1] to dynamically add peripherals and then measure and control them. In the second version, currently under development, InfluxDB was replaced with TimescaleDB, the REST API with GraphQL and the MQTT broker with WebSockets. The application is structured to separate the IoT aspect from the domain aspect (hydroponic greenhouses) to allow it to subsequently be broken out in a standalone service.

For the current roadmap, it will be used to visualize and allow the analysis of data covering the growth aspects of hydroponically grown plants. It is being developed as part of the [OpenFarmingAI research project](https://www.photonikforschung.de/projekte/open-innovation/projekt/openfarmingai.html) and will be receiving a project website in the coming weeks.

Aspects that are under development include an AR application to stream realtime data, a VR application to act as a learning platform for hydroponics and an AI to segment leaves and analyze a plants current health.

## ⚠️⚠️⚠️ Current Development Status ⚠️⚠️⚠️

In the current refactoring state it is recommended to follow the [core service documentation](./core/README.md). For a high-level overview, see the [Device Stacc post](https://hackernoon.com/device-stacc-a-reconfigurable-iot-platform-6j4e322p) on Hackernoon.

## Requirements

### Required

- **Docker:** available for [Ubuntu][2], [Mac][3], [Windows][4] and other [Linux flavors][5]. Note that currently only Ubuntu is supported.
- **Docker Compose:** the official [installation guide][6]
- **Python:** Version 3.8 and above (Django in core)
- **Secrets:** Secrets have to be provided for the grafana, influxdb, postgres and web services. Templates are provided and *should* be modified

For detailed instructions see the [server setup guide][7].

### Optional

- **SMTP server:** To enable user registration, credentials to an SMTP server are required. For testing purposes, the admin account may be used.

## Starting the Services

Start the complete setup with:

    ./start.sh development

Or in a production environment use:

    ./start.sh production

Stop the setup with:

    docker-compose down

List the individual services with `docker ps`. Key data to the individual services:

| Name              | Purpose                  | Port | Documentation               |
| ----------------- | ------------------------ | ---- | --------------------------- |
| core              | User management          | 8000 | [readme](core/README.md)    |
| grafana           | Time series analysis     | 3000 | [readme](grafana/README.md) |
| postgres          | User storage             | 5432 | N/A                         |
| influxdb          | Time series storage      | 8086 | N/A                         |
| redis             | Async task storage       |      | N/A                         |

The data is stored in volumes. List all active volumes with `docker volume ls`. To access Grafana, visit [localhost:3000](localhost:3000) after starting the services. The admin login credentials are defined in `web/secrets.flask`.

## Stopping the Development Services

Use `ctrl + C` to end the main server. The databases will remain as stopping them will clear their data. To stop them run `./start.sh clean`.


[1]: https://github.com/protohaus/sdg-controller
[2]: https://docs.docker.com/install/linux/docker-ce/ubuntu/
[3]: https://docs.docker.com/docker-for-mac/install/
[4]: https://docs.docker.com/docker-for-windows/install/
[5]: https://docs.docker.com/install/
[6]: https://docs.docker.com/compose/install/#install-compose
[7]: server_setup.md
[8]: https://semantic-ui.com/introduction/getting-started.html#installing
