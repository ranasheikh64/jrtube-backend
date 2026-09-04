# JRTube Backend

FastAPI backend service for JRTube video viewer with yt-dlp scraping and Redis caching.

---

## 🚀 Quick Start with Docker

### 1. Environment Setup
Copy the example environment file:
```bash
cp .env.example .env
```

### 2. Run with Docker Compose (Production Mode)
Starts both the FastAPI API and a Redis service:
```bash
docker compose up -d --build
```

- API Base URL: `http://localhost:8069`
- Interactive API Docs (Swagger): `http://localhost:8069/docs`
- Redoc: `http://localhost:8069/redoc`

### 3. Run with Docker Compose (Development Mode with Hot-Reload)
Mounts source files for live-reload:
```bash
docker compose -f docker-compose.dev.yml up --build
```

### 4. Stop Services
```bash
docker compose down
# Or to remove volumes as well:
docker compose down -v
```

---

## 🐳 Standalone Docker Usage

### Build Docker Image
```bash
docker build -t jrtube-backend .
```

### Run Standalone Container
```bash
docker run -d -p 8069:8069 --env-file .env --name jrtube-backend-container jrtube-backend
```

---

## ⚙️ Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PROJECT_NAME` | Project title in API documentation | `Video Viewer API` |
| `API_V1_STR` | API route prefix | `/api/v1` |
| `PORT` | Exposed host port | `8069` |
| `REDIS_URL` | Connection URL for Redis (Local or Upstash TLS) | `redis://redis:6379/0` |
| `CACHE_TTL_SECONDS` | Cache expiration time in seconds | `7200` (2 hours) |
| `YOUTUBE_COOKIES_BASE64` | Base64-encoded `cookies.txt` for YouTube authentication | `""` |
