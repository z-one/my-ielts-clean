# Docker Production Deployment

This directory contains the production Docker deployment for the IELTS app.

## First-time setup

1. Install Docker and Docker Compose on the server.
2. Copy or pull this repository onto the server.
3. Edit `docker/.env` and change at least:
   - `POSTGRES_PASSWORD`
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `CORS_ORIGINS`
   - `FRONTEND_PORT` if port `8080` is already used

`DATABASE_URL` must use the same password as `POSTGRES_PASSWORD`, and the host should stay as `postgres` when using this compose file.

PostgreSQL only applies `POSTGRES_PASSWORD` when the database volume is created for the first time. If you change the password after a volume already exists, either update the password inside PostgreSQL or recreate the volume with `down -v` after backing up any data you need.

## Start

From the repository root:

```bash
docker compose -f docker/docker-compose.yml --env-file docker/.env up -d --build
```

Open:

```text
http://SERVER_IP:8080
```

## Common operations

View logs:

```bash
docker compose -f docker/docker-compose.yml --env-file docker/.env logs -f
```

Restart after code changes:

```bash
docker compose -f docker/docker-compose.yml --env-file docker/.env up -d --build
```

Stop services:

```bash
docker compose -f docker/docker-compose.yml --env-file docker/.env down
```

Stop services and delete database data:

```bash
docker compose -f docker/docker-compose.yml --env-file docker/.env down -v
```

## Data persistence

PostgreSQL data is stored in the named Docker volume `docker_postgres-data`.
Backend logs are stored in the named Docker volume `docker_backend-logs`.
