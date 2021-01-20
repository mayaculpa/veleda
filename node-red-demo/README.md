# Node-RED Demo

This Node-RED demo is used to show the interaction with the GraphQL API. To use it, start a Node-RED instance (e.g. [in Docker](https://nodered.org/docs/getting-started/docker)) and then upload this file.

## Setup

To start a local Node-RED instance use the following command. It creates a Docker instance with persistant storage and uses the host networking so that it can access the server with its localhost address.

    docker run -d --network=host -v sdg-node_red_data:/data --name sdg-nodered nodered/node-red

Open a web browser at `127.0.0.1:1880` to see the Node-RED backend. First of all, the required node packages have to be installed. To install them, open the hamburger menu and select `Manage palette`. Select the `Install` tab and install the following nodes:

- node-red-dashboard
- node-red-contrib-moment
- node-red-contrib-graphql

Next, import the Node-RED flows. Open the hamburger menu in the top right and select import. Press `select a file to import` and choose the `flows.json` file in this directory. Then press import. The flows will be placed in the Home and other tabs. The `Flow 1` flow may be deleted by double clicking the tab and then selecting `Delete`.

One configuration has to be updated to be able to connect to the GraphQL endpoint. To do this go to the hamburger menu and select `Configuration nodes`. Then, double click the `SDG Server Dev` node under the `graphql-server` type. The endpoint has to be updated to the correct IP address and port of the core service. This can be found in `core/secrets.core` file under the `CORE_DOMAIN` environment variable. The authorization header is derived from the auth token in the core service (Django Admin → Auth Token → Tokens). To use the default token, copy the following into the `Authorization Header` field:

    Token: 543504d764fe2b729fac541f534f10a23fca4e6f
