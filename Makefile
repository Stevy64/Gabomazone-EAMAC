# ════════════════════════════════════════════
# GABOMAZONE — Commandes simplifiées
# Usage : make <commande>
# ════════════════════════════════════════════

.PHONY: help dev dev-build prod build migrate migrate-dev shell shell-dev superuser superuser-dev import-sqlite-dev logs logs-web logs-celery clean test collectstatic psql redis-cli

help:
	@echo "Commandes disponibles :"
	@echo "  make dev           - Lance l'environnement de développement"
	@echo "  make dev-build     - Reconstruit et lance en développement"
	@echo "  make prod          - Lance l'environnement de production"
	@echo "  make build         - Reconstruit les images Docker"
	@echo "  make migrate       - Applique les migrations (production)"
	@echo "  make migrate-dev   - Applique les migrations (développement)"
	@echo "  make shell         - Ouvre un shell Django (production)"
	@echo "  make shell-dev     - Ouvre un shell Django (développement)"
	@echo "  make superuser     - Crée un superutilisateur (production)"
	@echo "  make superuser-dev - Crée un superutilisateur (développement)"
	@echo "  make import-sqlite-dev - Importe db.sqlite3 → PostgreSQL dev"
	@echo "  make logs          - Affiche les logs en temps réel"
	@echo "  make logs-web      - Logs du service web uniquement"
	@echo "  make logs-celery   - Logs du worker Celery uniquement"
	@echo "  make clean         - Supprime les containers et volumes"
	@echo "  make test          - Lance les tests"
	@echo "  make collectstatic - Collecte les fichiers statiques"
	@echo "  make psql          - Ouvre un shell PostgreSQL"
	@echo "  make redis-cli     - Ouvre un shell Redis"

dev:
	docker compose -f docker-compose.dev.yml up

dev-build:
	docker compose -f docker-compose.dev.yml up --build

prod:
	docker compose up -d

build:
	docker compose build --no-cache

migrate:
	docker compose exec web python manage.py migrate

migrate-dev:
	docker compose -f docker-compose.dev.yml exec web python manage.py migrate

shell:
	docker compose exec web python manage.py shell

shell-dev:
	docker compose -f docker-compose.dev.yml exec web python manage.py shell

superuser:
	docker compose exec web python manage.py createsuperuser

superuser-dev:
	docker compose -f docker-compose.dev.yml run --rm web python manage.py createsuperuser

# Importe les données de l'ancienne BDD SQLite (db.sqlite3) vers PostgreSQL.
# Fonctionne même si le service web n'est pas démarré (utilise docker compose run).
# La BDD PostgreSQL (service db) doit être démarrée : make dev en arrière-plan ou
# docker compose -f docker-compose.dev.yml up -d db
import-sqlite-dev:
	@echo ">>> Import SQLite → PostgreSQL..."
	docker compose -f docker-compose.dev.yml run --rm web sh -c \
		"echo '>>> Mise à jour du schéma SQLite...' \
		 && USE_SQLITE=true python manage.py migrate --run-syncdb \
		 && echo '>>> Dump depuis SQLite...' \
		 && USE_SQLITE=true python manage.py dumpdata \
		  --exclude=contenttypes --exclude=auth.permission --exclude=sessions --exclude=admin \
		  --natural-foreign --natural-primary \
		  -o /tmp/sqlite_backup.json \
		 && echo '>>> Application des migrations PostgreSQL...' \
		 && python manage.py migrate --no-input \
		 && echo '>>> Purge des données PostgreSQL existantes...' \
		 && python manage.py flush --no-input \
		 && echo '>>> Import dans PostgreSQL...' \
		 && python manage.py loaddata /tmp/sqlite_backup.json \
		 && echo '>>> Import terminé.'"

logs:
	docker compose logs -f

logs-web:
	docker compose logs -f web

logs-celery:
	docker compose logs -f celery-worker

clean:
	docker compose down -v
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

test:
	docker compose -f docker-compose.dev.yml exec web python manage.py test --verbosity=2

collectstatic:
	docker compose exec web python manage.py collectstatic --noinput --clear

psql:
	docker compose exec db psql -U gabomazone gabomazone

redis-cli:
	docker compose exec redis redis-cli
