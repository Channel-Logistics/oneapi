### oneapi
Single Endpoint Satellite Tasking API

---

## Overview
oneapi provides a unified interface for satellite tasking and related services. The repository includes multiple services orchestrated with Docker Compose and a Makefile to streamline local development, builds, and testing.

## Prerequisites
- Docker and Docker Compose (Docker Desktop on macOS)
- Make (preinstalled on macOS; verify with `make -v`)

## Quick Start
Start all services (databases, message broker, backend services, client):
```bash
make up
```

Follow logs for all services:
```bash
make logs
```

Stop and remove containers and volumes:
```bash
make down
```

Rebuild containers:
```bash
make build
```

List running containers:
```bash
make ps
```

## Services and Ports
- **RabbitMQ**: AMQP `5672`, management UI `15672`
- **PostgreSQL**: `5432`
- **Adminer** (DB UI): `8080`
- **Gateway** (FastAPI): `8000`
- **Storage**: `9000`
- **Client** (Nginx): `3000`
- **Aggregator**, **Notifications**: background workers (no public ports)

Hot-reload for development is enabled via `docker-compose.override.yml` for `gateway`, `aggregator`, and `notifications` (code is bind-mounted into containers).

## Environment Variables
The following variables are used by services (set them in a local `.env` file at the repo root when needed):
- **AMQP_URL**: AMQP connection string (defaults to `amqp://user:pass@rabbitmq:5672`)
- **DATABASE_URL**: SQLAlchemy URL for storage (e.g., `postgresql+psycopg://app:app@postgres:5432/oneapi`)
- **SENDGRID_API_KEY**: Notifications email provider API key
- **NOTIFY_EMAIL_FROM**: Sender email address
- **NOTIFY_EMAIL_TO**: Recipient email address
- **APP_PORT**: Storage service port (defaults to `9000`)

Example `.env`:
```bash
AMQP_URL=amqp://user:pass@rabbitmq:5672
SENDGRID_API_KEY=your_sendgrid_key
NOTIFY_EMAIL_FROM=no-reply@example.com
NOTIFY_EMAIL_TO=you@example.com
```

## Available Makefile Commands
All commands assume Docker Compose. You can override the compose binary with `COMPOSE="docker compose"` (default) or `COMPOSE=docker-compose`.

- **Up**: start all services
  ```bash
  make up
  ```

- **Down**: stop and remove containers and volumes
  ```bash
  make down
  ```

- **Build**: build all images in parallel
  ```bash
  make build
  ```

- **Logs**: tail and follow logs
  ```bash
  make logs
  ```

- **PS**: list containers
  ```bash
  make ps
  ```

- **List test-enabled services**: shows all services from the merged compose config
  ```bash
  make list-test-services
  ```

- **Test (all or selected services)**:
  - Run tests for all core services (`aggregator`, `gateway`, `notifications`, `storage`):
    ```bash
    make test
    ```
  - Run tests for one service:
    ```bash
    make test TEST="gateway"
    ```
  - Shortcut target for a single service (auto-detects `*-tests` override service when present):
    ```bash
    make test-gateway
    make test-aggregator
    make test-notifications
    make test-storage
    ```

## Running Tests
Tests are executed inside service containers. The Makefile automatically prefers dedicated `*-tests` services defined in `docker-compose.override.yml` (which mount code for fast feedback) and falls back to running `pytest` inside the base service when no test service exists.

Examples:
```bash
# All services
make test

# Single service via TEST variable
make test TEST="gateway"

# Single service via shortcut target
make test-gateway
```

## Useful URLs
- Gateway API: `http://localhost:8000`
- Storage API: `http://localhost:9000`
- Client (static): `http://localhost:3000`
- RabbitMQ UI: `http://localhost:15672` (user/pass: `user`/`pass`)
- Adminer (DB UI): `http://localhost:8080` (server: `postgres`, user: `app`, password: `app`, db: `oneapi`)

## Troubleshooting
- If ports are in use, stop conflicting local services or change host ports in `docker-compose.yml`.
- If containers fail on first run, wait for health checks (RabbitMQ/Postgres) and try again.
- To reset local state (including database):
  ```bash
  make down && make up
  ```
