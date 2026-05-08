# ─── Teez Marketplace – Docker helper ─────────────────────
.PHONY: up down build restart logs shell db-shell update-modules

## Start all services (build if needed)
up:
	docker compose up -d --build

## Stop all services
down:
	docker compose down

## Rebuild the Odoo image
build:
	docker compose build --no-cache

## Restart Odoo only
restart:
	docker compose restart odoo

## Tail logs
logs:
	docker compose logs -f odoo

## Open a shell inside the Odoo container
shell:
	docker compose exec odoo bash

## Open psql inside the database container
db-shell:
	docker compose exec db psql -U odoo -d teez_marketplace

## Update / install specific modules  (usage: make update-modules MODS="odoo_marketplace")
update-modules:
	docker compose exec odoo odoo -u $(MODS) --stop-after-init -d teez_marketplace

## Install all three custom modules
install:
	docker compose exec odoo odoo -i odoo_marketplace,mobikul,mobikul_multi_vendor \
		--stop-after-init -d teez_marketplace

## Wipe volumes and start fresh  ⚠️  destroys all data
fresh:
	docker compose down -v
	docker compose up -d --build
