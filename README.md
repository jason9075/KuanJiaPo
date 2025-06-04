# KuanJiaPo

KuanJiaPo is a small experiment that detects faces from a camera and stores
those events in a MySQL database.  A FastAPI web service provides a simple
frontend for viewing the latest frame as well as previously captured events.

## Features

- Face detection powered by [DeepFace](https://github.com/serengil/deepface)
- FastAPI web API with a small HTML/JS interface
- MySQL database with initialization script under `config/mysql_init`
- Docker Compose setup for the detector, web server and database
- Optional `nix develop` shell for local development

## Requirements

- Docker and Docker Compose
- (optional) [Nix](https://nixos.org) if you want to use the provided flake

## Configuration

Create a `.env` file in the repository root and provide at least the following
variables used by `docker-compose.yml`:

```bash
MYSQL_ROOT_PASSWORD=changeme
MYSQL_DATABASE=kuanjiapo
MYSQL_USER=kuanjiapo
MYSQL_PASSWORD=kuanjiapo
# detector settings
INTERVAL_SEC=5
PERSON_INTERVAL_MIN=10
FACE_CONF_THR=0.6
```

`docker-compose.yml` injects these values into the containers.  The detector
also uses `SAVE_API_URL` to post events to the web API, which is already set to
`http://web:8000/api/save` when running through Docker Compose.

## Monitoring

The stack includes Prometheus and Grafana. Prometheus scrapes metrics from the
web server on port `8000/metrics` and from the detector on port `8001`. Grafana
is exposed on `http://localhost:3000` with Prometheus configured as a data
source.

## Running

Start the entire stack in the background using the Makefile target:

```bash
make dev
```

This command simply invokes Docker Compose as defined in
`docker-compose.yml`.  After the containers are up you can reach the web UI at
`http://localhost:8000`, phpMyAdmin at `http://localhost:8081`, Prometheus at
`http://localhost:9090` and Grafana at `http://localhost:3000`.

To stop and remove the containers use:

```bash
make stop
```

## Development with Nix

A `flake.nix` is provided which sets up a Python development environment.  Enter
it with:

```bash
nix develop
```

The shell hook creates a virtual environment and installs the dependencies from
`requirements.txt`.

## Repository layout

- `src/` – Python sources (`web.py` and `detect.py`)
- `static/` – HTML, CSS and JavaScript for the frontend
- `docker-compose.yml` – orchestrates the services
- `Dockerfile` – base image used for both web and detector services
- `Dockerfile.dev` – development image with hot reload using entr
- `config/prometheus.yml` – Prometheus scrape configuration
- `config/mysql_init/` – database initialization SQL
- `Makefile` – convenience targets for running and building the project

## License

This project is provided as-is without any warranty.
