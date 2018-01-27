# Grafana

In `env.grafana` change all `http://localhost:3000` instances to the root URL of your Grafana instance. In development environments this does not have to be changed. The `http://web:8001` address is used in Docker environments between the Grafana instance and the Flask web app.

## Environment Variables

Secrets are set in the `secrets.grafana` file while normal environment variables are set in `env.grafana`. A reference copy of the secrets file is provided as `secrets.grafana.example`. Change the values set there to random values specific to your setup.
