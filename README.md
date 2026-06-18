# Clan Communication Backend

Multi-tenant SaaS communication platform built with Python FastAPI microservices.  
Supports **1,000+ tenants** with minimal idle resource usage.

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    API Gateway / Ingress                   │
└────────────┬───────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────┐     Redis Streams / Pub-Sub
│  notification-service  │◄────────────────────────────┐
│   (orchestrator :8000) │                             │
└──┬──┬──┬──┬──┬─────────┘                             │
   │  │  │  │  │                                        │
   ▼  ▼  ▼  ▼  ▼                                        │
 email sms push in-app whatsapp                         │
  :8001 :8002 :8003 :8004 :8005                         │
                             │                          │
                             ▼                          │
                   whatsapp-webjs-service :3000          │
                                                        │
                   websocket-service :8006 ─────────────┘
```

## Services

| Service | Port | Description |
|---|---|---|
| `notification-service` | 8000 | Core orchestrator — routes to channel services |
| `email-service` | 8001 | SMTP / SendGrid / AWS SES with auto-failover |
| `sms-service` | 8002 | Twilio / Vonage / AWS SNS |
| `push-notification-service` | 8003 | FCM / APNS |
| `in-app-notification-service` | 8004 | Persistent in-app notifications + WebSocket push |
| `whatsapp-service` | 8005 | Python orchestration (Meta API + WebJS) |
| `websocket-service` | 8006 | Real-time WebSocket gateway (Redis pub/sub fan-out) |
| `whatsapp-webjs-service` | 3000 | Node.js WhatsApp Web.js persistent browser session |

## Quick Start

```bash
# 1. Copy environment files
cp config/environments/local.env.example .env

# 2. Start the entire stack
make up

# 3. Run migrations
make migrate

# 4. Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health
```

## Multi-Tenant Usage

Every request must include:

```http
X-Tenant-ID: tenant-abc-123
X-API-Key: your-api-key
```

### Send a notification

```bash
curl -X POST http://localhost:8000/api/v1/notifications \
  -H "X-Tenant-ID: tenant-abc" \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_id": "user-001",
    "channel": "email",
    "subject": "Welcome!",
    "body": "Thank you for joining."
  }'
```

### Send bulk notifications

```bash
curl -X POST http://localhost:8000/api/v1/notifications/bulk \
  -H "X-Tenant-ID: tenant-abc" \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "notifications": [
      {"recipient_id": "user-001", "channel": "email", "subject": "Hi", "body": "..."},
      {"recipient_id": "user-002", "channel": "sms", "body": "Your code: 123456"}
    ]
  }'
```

### WebSocket real-time connection

```javascript
const ws = new WebSocket("ws://localhost:8006/ws/{tenant_id}/{recipient_id}");
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

## Development Commands

```bash
make up            # Start all services
make down          # Stop all services
make build         # Rebuild Docker images
make test          # Run tests
make migrate       # Apply DB migrations
make lint          # Lint Python code (ruff)
make format        # Format Python code (ruff)
make logs SERVICE=email-service   # Stream logs
make clean         # Remove everything
```

## Adding a New Service

1. Copy `templates/service-template/` to `services/<new-service>/`
2. Replace `{{service-name}}` placeholders
3. Add to `docker-compose.yml`
4. Add path filter in `.github/workflows/ci.yml`
5. Add Helm entry in `deploy/helm/values.yaml`

## Tech Stack

- **Runtime**: Python 3.12, FastAPI, SQLAlchemy 2 (async), Alembic
- **Databases**: PostgreSQL (per service), Redis (event bus + cache)
- **Messaging**: Redis Streams for inter-service events
- **Container**: Docker multi-stage builds, Kubernetes + Helm
- **Node.js services**: Express 4, whatsapp-web.js
- **CI/CD**: GitHub Actions with path-filtered builds
