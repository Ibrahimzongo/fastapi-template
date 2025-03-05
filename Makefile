.PHONY: help build up down logs shell test test-unit test-cov fmt lint clean

# Variables
SERVICE_NAME := api

help: ## Affiche une aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Construit les images Docker
	docker-compose build

up: ## Démarre les conteneurs en mode détaché
	docker-compose up -d

down: ## Arrêter les conteneurs
	docker-compose down

logs: ## Affiche les logs des conteneurs
	docker-compose logs -f

shell: ## Ouvre un shell dans le conteneur de l'application
	docker-compose exec $(SERVICE_NAME) bash

test: ## Exécute tous les tests
	docker-compose exec $(SERVICE_NAME) pytest -v

test-unit: ## Exécute les tests unitaires
	docker-compose exec $(SERVICE_NAME) pytest tests/unit -v

test-cov: ## Exécute les tests avec couverture
	docker-compose exec $(SERVICE_NAME) pytest --cov=src tests/

fmt: ## Formate le code avec black
	docker-compose exec $(SERVICE_NAME) black src/ tests/

lint: ## Vérifie le code avec flake8
	docker-compose exec $(SERVICE_NAME) flake8 src/ tests/

clean: ## Supprime les conteneurs, volumes et images
	docker-compose down -v
	docker system prune -f
	

migrate: ## Exécute les migrations alembic
	docker-compose exec $(SERVICE_NAME) alembic upgrade head

makemigrations: ## Crée une nouvelle migration
	docker-compose exec $(SERVICE_NAME) alembic revision --autogenerate -m "$(message)"

start-prod: ## Démarre l'environnement de production
	docker-compose -f docker-compose.prod.yml up -d

logs-prod: ## Affiche les logs de production
	docker-compose -f docker-compose.prod.yml logs -f