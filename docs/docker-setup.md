# Docker & Docker Compose Setup Guide

OpenCitizen AI provides container orchestration via Docker Compose to manage persistent services:
- **PostgreSQL 16 (Alpine)**: Relational application metadata and audit persistence.
- **Qdrant v1.12**: Vector similarity search engine for semantic passage retrieval.

---

## 1. Prerequisites

- **Docker Engine** (>= 24.0)
- **Docker Compose** (>= v2.20)
- Verify Docker is running:
  ```bash
  docker --version
  docker compose version
  ```

---

## 2. Docker Compose Configuration

The root `docker-compose.yml` configures two persistent services:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: opencitizen-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-opencitizen}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-opencitizen_dev_password}
      POSTGRES_DB: ${POSTGRES_DB:-opencitizen_app}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-opencitizen} -d ${POSTGRES_DB:-opencitizen_app}"]
      interval: 5s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:v1.12.0
    container_name: opencitizen-qdrant
    restart: unless-stopped
    environment:
      QDRANT__SERVICE__GRPC_PORT: 6334
    ports:
      - "${QDRANT_PORT:-6333}:6333"
      - "${QDRANT_GRPC_PORT:-6334}:6334"
    volumes:
      - qdrant_storage:/qdrant/storage
    healthcheck:
      test: ["CMD-SHELL", "bash -c 'exec 3<>/dev/tcp/localhost/6333' || exit 1"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
    name: opencitizen_postgres_data
  qdrant_storage:
    name: opencitizen_qdrant_storage
```

---

## 3. Starting the Services

### 3.1 Start Services in the Background
From the workspace root:
```bash
docker compose up -d
```

### 3.2 Verify Container Status
Check that both containers are healthy:
```bash
docker compose ps
```
Expected output:
```
NAME                   IMAGE                    COMMAND                  SERVICE    STATUS
opencitizen-postgres   postgres:16-alpine       "docker-entrypoint.s…"   postgres   Up (healthy)
opencitizen-qdrant     qdrant/qdrant:v1.12.0    "./qdrant"               qdrant     Up (healthy)
```

### 3.3 Verify Service Health Endpoints
- **Qdrant HTTP REST API**: `curl http://localhost:6333/healthz`
- **Qdrant Web Dashboard**: Open [http://localhost:6333/dashboard](http://localhost:6333/dashboard) in your browser.
- **Postgres Health**: `docker exec -it opencitizen-postgres pg_isready -U opencitizen -d opencitizen_app`

---

## 4. Running Database Migrations

Once PostgreSQL is healthy, apply Alembic database migrations:
```bash
cd backend
alembic upgrade head
cd ..
```

---

## 5. Connecting the Backend Application

In your `.env` file, ensure the connection parameters match the Docker Compose setup:
```env
DATABASE_URL=postgresql://opencitizen:opencitizen_dev_password@localhost:5432/opencitizen_app
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_IN_MEMORY=false
```

Start the backend:
```bash
uvicorn backend.app.main:app --reload --port 8000
```

---

## 6. Stopping and Resetting Services

### Stop Containers
```bash
docker compose down
```

### Reset Data Volumes (Destructive)
To completely wipe PostgreSQL records and Qdrant vector collections:
```bash
docker compose down -v
```

---

## 7. Troubleshooting

### Port Conflicts (5432 or 6333 already in use)
If you already have a local PostgreSQL or Qdrant instance running on your machine:
1. Update `.env` with alternative host ports:
   ```env
   POSTGRES_PORT=5433
   QDRANT_PORT=6335
   ```
2. Restart Compose:
   ```bash
   docker compose up -d
   ```
3. Update `DATABASE_URL` and `QDRANT_PORT` in your backend configuration accordingly.
