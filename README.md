# KuanJiaPo

KuanJiaPo is a small experiment that detects faces from a camera and stores
those events in a MySQL database. A FastAPI web service provides a simple
frontend for viewing the latest frame as well as previously captured events.

## Features

- Face detection powered by [DeepFace](https://github.com/serengil/deepface)
- FastAPI web API with a small HTML/JS interface
- MySQL database with initialization script under `config/mysql_init`
- Docker Compose setup for the detector, web server and database
- Optional `nix develop` shell for local development
- Experimental two-way voice chat using WebRTC
- Append `?autocall=true` to automatically start the voice call

## Requirements

- Docker and Docker Compose
- (optional) [Nix](https://nixos.org) if you want to use the provided flake
- `uvicorn[standard]` or another WebSocket library for voice chat

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
OFF_HOURS_INTERVAL_SEC=15
FRAME_DIFF_THR=15
# https certificate (optional)
SSL_CERTFILE=./certs/server.crt
SSL_KEYFILE=./certs/server.key
REMINDER_AUDIO_DIR=./static/reminders
REMINDER_CHECK_INTERVAL=60
```

`docker-compose.yml` injects these values into the containers. The detector
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
`docker-compose.yml`. After the containers are up you can reach the web UI at
`http://localhost:8000`, phpMyAdmin at `http://localhost:8081`, Prometheus at
`http://localhost:9090` and Grafana at `http://localhost:3000`.

To stop and remove the containers use:

```bash
make stop
```

## Reminders

Visit `http://localhost:8000/reminder` to schedule weekly audio reminders.
Upload an MP3 file, choose the day of week and the time of day (HH:MM). The
server stores reminders in MySQL and plays them automatically at the scheduled
time. Each playback is counted by the `reminders_played_total` Prometheus
metric. Reminder audio files are stored under `static/reminders` (configurable
via `REMINDER_AUDIO_DIR`).

## HTTPS Setup

The web server can run over HTTPS by providing a certificate and key. Docker
Compose expects them at `./certs/server.crt` and `./certs/server.key`. You can
create your own certificate authority (CA) and sign the server certificate:

```bash
# generate CA
openssl genrsa -out certs/ca.key 2048
openssl req -x509 -new -nodes -key certs/ca.key -days 3650 -out certs/ca.crt -subj "/CN=Home CA"

# generate server certificate signed by the CA
openssl genrsa -out certs/server.key 2048
openssl req -new -key certs/server.key -out certs/server.csr -subj "/CN=jasonkuan"
openssl x509 -req -in certs/server.csr -CA certs/ca.crt -CAkey certs/ca.key -CAcreateserial -out certs/server.crt -days 3650 -extfile san.ext
```

On Windows, open `mmc.exe`, add the "Certificates" snap-in for the local
computer and import `ca.crt` under "Trusted Root Certification Authorities".
For Android, copy `ca.crt` to the device and install it via
**Settings → Security → Encryption & credentials → Install a certificate → CA certificate**.

After placing the files, run `make dev` again and browse to
`https://localhost:8000`.

## Development with Nix

A `flake.nix` is provided which sets up a Python development environment. Enter
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

## Enabling WebRTC Puppeteer Client on Boot (User-level systemd)

If you want the device to automatically join the WebRTC voice call on boot (with real microphone and speaker), you can use a user-level systemd service.

### Step 1: Enable user lingering (so user services run at boot)

```bash
sudo loginctl enable-linger $(whoami)
```

### Step 2: Create the service file

Save the following content to:

```bash
~/.config/systemd/user/webrtc-client.service
```

```ini
[Unit]
Description=WebRTC Puppeteer Headless Client with Xvfb
After=network-online.target
Wants=network-online.target

[Service]
Environment=DISPLAY=:99
ExecStartPre=/run/current-system/sw/bin/sleep 60
ExecStart=/home/jason9075/.nix-profile/bin/xvfb-run -s "-screen 0 1024x768x24" node /home/jason9075/KuanJiaPo/puppeteer-client.js
WorkingDirectory=/home/jason9075/KuanJiaPo
RestartSec=5
KillSignal=SIGINT
TimeoutStopSec=10

[Install]
WantedBy=default.target
```

### Step 3: Enable and start the service

```bash
systemctl --user daemon-reload
systemctl --user enable webrtc-client.service
systemctl --user start webrtc-client.service
```

This will automatically start the Puppeteer WebRTC client on boot and connect to the server with audio support, assuming a microphone and speaker are available and Chromium is correctly configured.

## License

This project is provided as-is without any warranty.
