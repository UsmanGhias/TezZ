# ─── TezZ Marketplace – developer helper ─────────────────────
.PHONY: help up up-dev up-proxy down build restart logs shell db-shell \
        update-modules install fresh \
        api-test api-install \
        flutter-get flutter-run flutter-test flutter-lint flutter-build-apk \
        seed env

DEFAULT_DB ?= teez_marketplace

help:  ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ─── Environment ─────────────────────────────────────────────
env:  ## Create .env from .env.example if missing.
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example")

# ─── Docker stack ────────────────────────────────────────────
up: env  ## Start the core stack (db, redis, odoo).
	docker compose up -d --build

up-dev: env  ## Start core stack + pgAdmin.
	docker compose --profile dev up -d --build

up-proxy: env  ## Start core stack + nginx reverse proxy.
	docker compose --profile proxy up -d --build

down:  ## Stop all services.
	docker compose down

build:  ## Rebuild the Odoo image.
	docker compose build --no-cache

restart:  ## Restart Odoo only.
	docker compose restart odoo

logs:  ## Tail Odoo logs.
	docker compose logs -f odoo

shell:  ## Open a shell inside the Odoo container.
	docker compose exec odoo bash

db-shell:  ## Open psql inside the database container.
	docker compose exec db psql -U $${POSTGRES_USER:-odoo} -d $(DEFAULT_DB)

update-modules:  ## Update modules: `make update-modules MODS="tezz_api"`.
	docker compose exec odoo odoo -u $(MODS) --stop-after-init -d $(DEFAULT_DB)

install:  ## Install all custom Odoo modules.
	docker compose exec odoo odoo -i odoo_marketplace,mobikul,mobikul_multi_vendor,tezz_api \
		--stop-after-init -d $(DEFAULT_DB)

fresh:  ## ⚠ Wipe volumes and start fresh — destroys all data.
	docker compose down -v
	docker compose up -d --build

# ─── tezz_api ────────────────────────────────────────────────
api-install:  ## Install / upgrade the tezz_api module.
	docker compose exec odoo odoo -i tezz_api --stop-after-init -d $(DEFAULT_DB)

api-test:  ## Run tezz_api tests (HttpCase) inside the Odoo container.
	docker compose exec odoo odoo --test-enable --test-tags tezz_api \
		-i tezz_api --stop-after-init -d $(DEFAULT_DB)

# ─── Flutter ─────────────────────────────────────────────────
flutter-get:  ## flutter pub get
	cd teez_flutter && flutter pub get

flutter-run:  ## flutter run (uses connected device/emulator)
	cd teez_flutter && flutter run

flutter-test:  ## flutter test
	cd teez_flutter && flutter test

flutter-lint:  ## flutter analyze + dart format check
	cd teez_flutter && flutter analyze && dart format --set-exit-if-changed lib test

flutter-build-apk:  ## Release APK
	cd teez_flutter && flutter build apk --release

# ─── Data ────────────────────────────────────────────────────
seed:  ## Run the demo-data seed script inside Odoo.
	docker compose exec odoo python3 /mnt/extra-addons/../scripts/seed_demo.py
