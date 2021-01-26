[![Build Status](https://travis-ci.org/FlowLeaf/flow-leaf-server.svg?branch=master)](https://travis-ci.org/FlowLeaf/flow-leaf-server)
[![codecov](https://codecov.io/gh/FlowLeaf/flow-leaf-server/branch/master/graph/badge.svg)](https://codecov.io/gh/FlowLeaf/flow-leaf-server)

# SmartDigitalGarden / DeviceStacc Server

A data analytics platform for hydroponic setups. It visualizes and allows analysis of data covering the growth aspects of hydroponics. It creates a system that covers the data collection and automation to data storage and analysis.

## ⚠️⚠️⚠️ Current Development Status ⚠️⚠️⚠️

In the current refactoring state it is recommended to follow the [core service documentation](./core/README.md). For a high-level overview, see the Device Stacc post on Hackernoon.

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


[2]: https://docs.docker.com/install/linux/docker-ce/ubuntu/
[3]: https://docs.docker.com/docker-for-mac/install/
[4]: https://docs.docker.com/docker-for-windows/install/
[5]: https://docs.docker.com/install/
[6]: https://docs.docker.com/compose/install/#install-compose
[7]: server_setup.md
[8]: https://semantic-ui.com/introduction/getting-started.html#installing
