# railway-iot-django-api

Django 5 REST API + ASGI backend for **railway-iot-platform**.

---

## Responsibilities

- MQTT message ingestion via `paho-mqtt` subscriber
- REST API with Django REST Framework + JWT authentication
- Real-time push via Django Channels WebSockets
- Celery task dispatch for persistence and alert rules
- Security audit logging middleware

---

## Stack

| Component | Library / Version |
|---|---|
| Web framework | Django 5.x |
| REST API | Django REST Framework |
| Authentication | `djangorestframework-simplejwt` |
| ASGI server | Daphne |
| WebSocket | Django Channels + Redis channel layer |
| MQTT client | `paho-mqtt` |
| Task queue | Celery (dispatch only; workers in `railway-iot-celery-worker`) |
| Database | TimescaleDB via `psycopg2` |
| Config | `python-decouple` |

---

## Project Layout

```
src/
├── core/
│   ├── settings.py       ← Django settings (security-hardened)
│   ├── urls.py           ← URL routing incl. JWT auth endpoints
│   ├── asgi.py           ← ASGI app with JWT WebSocket middleware
│   ├── ws_auth.py        ← JWTAuthMiddleware for Django Channels
│   └── middleware.py     ← SecurityAuditMiddleware
└── apps/
    ├── telemetry/        ← Readings, devices, zones API + MQTT consumer
    ├── alerts/           ← Alerts API + WebSocket consumer
    └── tasks/
        ├── ingest.py     ← persist_reading Celery task
        └── alert_rules.py ← check_threshold_alert Celery task
```

---

## API Endpoints

### Authentication

```
POST /api/v1/auth/token/          → {"access": "...", "refresh": "..."}
POST /api/v1/auth/token/refresh/  → {"access": "..."}
```

All other endpoints require:
```
Authorization: Bearer <access_token>
```

### Telemetry

```
GET  /api/v1/readings/            List sensor readings
GET  /api/v1/readings/latest/     Latest reading per device
GET  /api/v1/zones/               List zones
GET  /api/v1/devices/             List devices
```

### Alerts

```
GET   /api/v1/alerts/             List alerts (?acknowledged=false&limit=50)
GET   /api/v1/alerts/<id>/        Alert detail
PATCH /api/v1/alerts/<id>/        Acknowledge: {"acknowledged": true}
```

---

## WebSocket Endpoints

All WebSocket connections require `?token=<jwt>` in the URL. Unauthenticated connections are closed with code `4401`.

```
ws://localhost:8003/ws/telemetry/?token=<access_token>
ws://localhost:8003/ws/alerts/?token=<access_token>
```

Messages are JSON-encoded `SensorReading` objects pushed as new readings arrive.

---

## Security

### Input Validation
- `device_id` and `zone` validated with regex `^[\w\-]{1,64}$`
- Metric names validated against whitelist: `temperature`, `vibration`, `rpm`, `brake-pressure`, `load-weight`
- MQTT payloads validated before persistence (required fields, type bounds, ISO timestamp)
- Invalid payloads are silently dropped — no error surfaces to external clients

### Authentication & Authorization
- `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` — all endpoints authenticated by default
- JWT access token lifetime: **60 minutes**; refresh token lifetime: **1 day**
- Token blacklist enabled for logout support

### Rate Limiting
- Anonymous: 30 req/min
- Authenticated: 300 req/min
- Additional Nginx-level rate limits (see infra README)

### Audit Logging
`SecurityAuditMiddleware` logs to stdout:
- All `401` and `403` responses (with client IP and path)
- All write operations: `POST`, `PUT`, `PATCH`, `DELETE` (with authenticated username)

### Other Hardening
- `DEBUG` defaults to `False`; `SECRET_KEY` has no default (server refuses to start if unset)
- `CORS_ALLOW_ALL_ORIGINS = False`; origins explicitly whitelisted
- `SECURE_BROWSER_XSS_FILTER = True`, `X_FRAME_OPTIONS = "DENY"`
- `CSRF_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_HTTPONLY = True`

---

## Local Dev (without Docker)

```bash
cd src
pip install -r ../requirements.txt

# Requires DB, Redis, and MQTT running
export $(cat ../../railway-iot-infra/.env | xargs)

python manage.py migrate
python manage.py createsuperuser
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

---

## MQTT Topic Schema

The Django MQTT consumer subscribes to `rail/#` and expects payloads in this format:

```json
{
  "device_id": "track-sensor-01",
  "zone": "zone-a",
  "metric": "temperature",
  "value": 68.4,
  "timestamp": "2026-03-17T10:30:00Z"
}
```
