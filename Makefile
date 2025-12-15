#!/usr/bin/make

include .env
export $(shell sed 's/=.*//' .env)

SHELL = /bin/sh

MAIN_COMPOSE= docker-compose.yaml
COMPOSES=-f $(MAIN_COMPOSE)
SERVICES := app db redis celery-worker celery-beat
CONTAINER=atraks_app
MANAGE=python /app/src/kernel/manage.py

COLOR_RESET = \033[0m
COLOR_GREEN = \033[32m
COLOR_YELLOW = \033[33m
COLOR_WHITE = \033[00m

.PHONY: up down logs clear  migrations migrate csu env app help update_rossvyaz

app: # run app services
	docker compose -f $(MAIN_COMPOSE) --profile app
up: # run all services
	docker compose -f $(MAIN_COMPOSE) --profile all up -d --force-recreate --build --remove-orphans $(SERVICES)
down: # stop all services
	docker compose $(COMPOSES) --profile all down -v
logs: # get last logs
	docker compose $(COMPOSES) --profile all logs -f

migrations: # make migration
	docker exec -it $(CONTAINER) $(MANAGE) makemigrations
migrate: # run migrations
	docker exec -it $(CONTAINER) $(MANAGE) migrate
csu: # create superuser
	docker exec -it $(CONTAINER) $(MANAGE) csu

update_rossvyaz: # fetch rossvyaz data
	docker exec -it $(CONTAINER) $(MANAGE) update_rossvyaz


.PHONY: prune
prune:
	docker compose down -v --remove-orphans
	- docker images --format "{{.Repository}}:{{.Tag}}" | grep '^atrakstrade-' | xargs -r docker rmi -f
	docker image prune -f


env: # setup env file
	@mv .env_example .env


help: # show help
	@echo -e "$(COLOR_GREEN)Makefile help:"
	@grep -E "^[a-zA-Z0-9 -]+:.*#"  Makefile | sort | while read -r l; do printf "$(COLOR_GREEN)  $$(echo $$l | cut -f 1 -d':'):$(COLOR_WHITE)$$(echo $$l | cut -f 2- -d'#')\n"; done
