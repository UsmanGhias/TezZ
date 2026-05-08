# TezZ — Multi-Vendor Marketplace

A scalable, mobile-first marketplace built on top of Odoo 17 and the
Webkul multi-vendor addons, with a Flutter customer + vendor app and a
versioned REST API designed for production.

```
Flutter App ──► Nginx ──► Odoo (tezz_api) ──► PostgreSQL
                                  │
                                  └──► Redis (cache / rate-limit)
```

---

## Repository layout

| Path                                 | Purpose                                                                 |
| ------------------------------------ | ----------------------------------------------------------------------- |
| `multi_vendor_App/`                  | Odoo addons — mounted at `/mnt/extra-addons` in the Odoo container.     |
| `multi_vendor_App/tezz_api/`         | **TezZ REST API** module (JWT auth + `/api/v1/*`).                      |
| `multi_vendor_App/odoo_marketplace/` | Webkul Marketplace base.                                                |
| `multi_vendor_App/mobikul*`          | Webkul Mobikul mobile-API addons (legacy, used by older app builds).    |
| `multi_vendor_App/teezz_theme/`      | TezZ-branded website theme.                                             |
| `teez_flutter/`                      | **Flutter app — source of truth** (Riverpod + go_router).               |
| `teez_mobile_app/`                   | Legacy native Android prototype, kept for reference; not actively built.|
| `deploy/nginx/`                      | Reverse-proxy configuration for production.                             |
| `scripts/`                           | Operational scripts (e.g. `seed_demo.py`).                              |
| `docker-compose.yml`, `Dockerfile`   | Local + production container topology.                                  |
| `Makefile`                           | Developer commands (`make help`).                                       |
| `.env.example`                       | Environment-variable template.                                          |

---

## Services & ports

| Service  | Port (host) | Notes                                                |
| -------- | ----------- | ---------------------------------------------------- |
| Odoo     | `8069`      | Web client + `/api/v1/*` mobile API                  |
| Odoo     | `8072`      | Long-polling / live chat                             |
| Postgres | *internal*  | Reachable from Odoo only                             |
| Redis    | *internal*  | Cache + rate-limit backend                           |
| pgAdmin  | `5050`      | `--profile dev`, default login from `.env`           |
| Nginx    | `80/443`    | `--profile proxy`, terminates TLS for production     |

---

## Quick start (local development)

### 1. Configure environment

```bash
cp .env.example .env
$EDITOR .env          # set passwords + JWT secret
```

### 2. Bring up the backend

```bash
make up               # core stack (db, redis, odoo)
# or
make up-dev           # adds pgAdmin on :5050
```

### 3. Install the custom Odoo modules

After the first `make up`, create the database via `http://localhost:8069`
(use the master password from `.env`), then:

```bash
make install          # installs odoo_marketplace, mobikul*, tezz_api
```

### 4. Run the Flutter app against your local Odoo

The mobile app cannot reach `localhost` from a phone or emulator; use your
machine's LAN IP (e.g. `192.168.1.5`) and pass it through `--dart-define`:

```bash
make flutter-get
cd teez_flutter
flutter run --dart-define=API_BASE_URL=http://192.168.1.5:8069
```

> **Tip:** the same value should match `API_BASE_URL` in your `.env` so all
> dev tooling stays consistent.

---

## TezZ API (`tezz_api`)

A new versioned JSON REST surface that the Flutter apps consume. Highlights:

- Base path: `/api/v1/`
- JWT auth (HS256) with rotating refresh tokens
- Role-based access via `@tezz_jwt_required(role="customer"|"vendor"|"admin")`
- Consistent envelope `{data, error, meta}` and stable error codes
- Rate-limited auth/OTP endpoints

Run the test suite:

```bash
make api-test
```

See [`multi_vendor_App/tezz_api/README.md`](multi_vendor_App/tezz_api/README.md)
and [`multi_vendor_App/tezz_api/static/openapi.yaml`](multi_vendor_App/tezz_api/static/openapi.yaml)
for the full endpoint catalog.

### Smoke check

```bash
curl -s http://localhost:8069/api/v1/health | jq
# → { "data": { "status": "ok", ... }, "error": null, "meta": { ... } }

curl -s -XPOST http://localhost:8069/api/v1/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"email":"admin","password":"admin"}' | jq
```

---

## Common Make targets

```text
make help              List all targets
make up                Start core stack
make up-dev            Start core stack + pgAdmin
make up-proxy          Start core stack + nginx
make down              Stop everything
make logs              Tail Odoo logs
make shell             Bash inside Odoo container
make db-shell          psql inside Postgres container
make install           Install all custom Odoo modules
make api-install       Install / upgrade tezz_api only
make api-test          Run tezz_api HttpCase tests
make flutter-get       flutter pub get
make flutter-run       flutter run (LAN device / emulator)
make flutter-test      flutter test
make flutter-lint      flutter analyze + dart format check
make flutter-build-apk Release APK
make fresh             ⚠ Wipe volumes and restart
```

---

## Env-var conventions

- **Backend secrets** live in `.env` and are consumed by `docker compose`.
- **Mobile build-time values** are passed via `flutter --dart-define=KEY=VALUE`.
- **JWT signing secret** must be set via `tezz_api.jwt_secret` (system parameter
  in Odoo) for production. A random one is generated on first use otherwise.
- Never commit `.env`, `*.pem`, `*.p12`, or any provider service-account JSON.

---

## Deployment

The `docker-compose.yml` is production-shaped: enable the `proxy` profile to
front the stack with nginx (`make up-proxy`), drop TLS certificates in
`deploy/nginx/ssl/`, and uncomment the HTTPS server block in
`deploy/nginx/conf.d/tezz.conf`.

For VPS provisioning recommendations (DigitalOcean / Hetzner / Contabo) and
release pipelines, see the project plan tracked in the repository's PRs.
