.DEFAULT_GOAL:=help

.PHONY: dev
dev:						## Run the application in development mode
	@echo "Running the application in development mode..."
	@docker compose -f docker-compose.yml up -d

.PHONY: run
run:						## Run all the application
	@docker inspect --type container kuanjiapo-detect > /dev/null 2>&1 && \
		echo "The application is already running" || \
		echo "Running the application..."
	@docker compose -f docker-compose.yml up -d

.PHONY: build
build:						## Build the docker image
	@docker compose build -f docker-compose-dev.yml

.PHONY: stop
stop:						## Stop the application
	@echo "Stopping the application..."
	@docker compose down --volumes

.PHONY: unit-test
unit-test:					## Run unit tests
	@echo "Running unit tests..."

.PHONY: integration-test
integration-test:			## Run integration tests
	@echo "Running integration tests..."

.PHONY: help
help:						## Show this help
	@echo "Makefile for local development"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m (default: help)\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
