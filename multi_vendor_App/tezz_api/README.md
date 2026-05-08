# tezz_api — TezZ Marketplace REST API

A custom Odoo 17 module that exposes a clean, versioned, JSON REST surface
for the TezZ Flutter customer and vendor apps. It sits **on top of** the
Webkul marketplace addons (`odoo_marketplace`, `mobikul`, `mobikul_multi_vendor`)
and is upgrade-safe — it never modifies their code.

## Highlights

- **Versioned base path:** `/api/v1/...`
- **JWT auth** with rotating refresh tokens (HS256, configurable secret)
- **Role-based access** via `@tezz_jwt_required(role="customer"|"vendor"|"admin")`
- **Consistent envelope** `{data, error, meta}` with stable error codes
- **Rate limiting** on auth/OTP endpoints (DB-backed, Redis-swappable)
- **Lazy** integration with Webkul models — works even when they aren't installed

## Install

1. Drop this folder under your Odoo addons path (the repo's `multi_vendor_App/`
   is mounted at `/mnt/extra-addons` by `docker-compose.yml`).
2. Install the PyJWT dependency in the Odoo image — it's already added to the
   top-level `Dockerfile`.
3. Install the module:

   ```bash
   make update-modules MODS=tezz_api
   # or
   docker compose exec odoo odoo -i tezz_api -d teez_marketplace --stop-after-init
   ```

## Configuration

System parameters (settable via `Settings → Technical → Parameters`):

| Key | Default | Purpose |
|---|---|---|
| `tezz_api.jwt_secret` | *(generated on first use)* | HS256 signing secret |
| `tezz_api.jwt_issuer` | `tezz-api`                  | `iss` claim |
| `tezz_api.access_ttl` | `1800`                      | Access token TTL (seconds) |
| `tezz_api.refresh_ttl` | `2592000`                  | Refresh token TTL (seconds) |
| `tezz_api.rl.login.per_minute` | `10`               | Login attempts per IP per minute |
| `tezz_api.rl.signup.per_hour`  | `5`                | Signups per IP per hour |
| `tezz_api.rl.otp.per_hour`     | `5`                | OTP requests per IP per hour |

> ⚠️ **Production:** explicitly set `tezz_api.jwt_secret` to a long random
> value. The default is generated on first use and logged at WARNING.

## Endpoint summary

See [`static/openapi.yaml`](static/openapi.yaml) for the canonical spec.
Main groups:

- `auth/*` — signup, login, refresh, logout, forgot, reset, OTP
- `auth/oauth/{google|facebook|apple}` — social login (provider verification stubbed)
- `home`, `categories`, `products`, `products/<id>`, `products/search`
- `cart`, `cart/items`, `cart/items/<id>`
- `checkout/quote`, `checkout/place`
- `orders`, `orders/<id>`, `orders/<id>/track`, `orders/<id>/cancel`
- `me`, `me/addresses`, `me/wishlist`
- `vendor/dashboard`, `vendor/products`, `vendor/orders`, `vendor/wallet`
- `payments/intents`, `payments/webhooks/<provider>`
- `devices` (FCM token registration)

## Auth flow

```
POST /api/v1/auth/login
→ { access_token, refresh_token, ... }

GET  /api/v1/me            (Authorization: Bearer <access_token>)
POST /api/v1/auth/refresh  (body: { refresh_token })
POST /api/v1/auth/logout   (body: { refresh_token })
```

Refresh tokens are stored hashed (`tezz.refresh_token`); rotation revokes the
previous token, so a stolen refresh token is invalidated as soon as the
legitimate client refreshes.

## Tests

```bash
docker compose exec odoo odoo \
  --test-enable --test-tags tezz_api \
  -i tezz_api -d teez_marketplace --stop-after-init
```

## Roadmap (handled in follow-up PRs)

- Real provider verification for Google/Facebook/Apple OAuth
- JazzCash / Easypaisa / Stripe / PayPal / Razorpay payment-intent integrations
- Banner CMS model (`tezz.banner`) replacing the empty `home.banners` array
- Notification fan-out via FCM HTTP v1 + `queue_job`
- Redis-backed rate limiter
- Per-endpoint OpenAPI request/response schemas
