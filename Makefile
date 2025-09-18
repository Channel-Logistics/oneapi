# Services that can have tests (exclude client/nginx)
SERVICES := aggregator gateway notifications storage
COMPOSE ?= docker compose

.PHONY: up down build logs ps test test-% list-test-services

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down -v

build:
	$(COMPOSE) build --parallel

logs:
	$(COMPOSE) logs -f --tail=200

ps:
	$(COMPOSE) ps

# Show services available in the merged compose config (includes override)
list-test-services:
	@$(COMPOSE) config --services

# Run tests for all or some services.
# Uses <service>-tests from docker-compose.override.yml when present,
# otherwise falls back to running pytest inside <service>.
# Examples:
#   make test                    -> run tests for all SERVICES
#   make test TEST="gateway"     -> only gateway
test:
	@set -e; \
	SVCS="$(if $(TEST),$(TEST),$(SERVICES))"; \
	ALL_SERVICES="$$( $(COMPOSE) config --services )"; \
	for s in $$SVCS; do \
	  echo ">> Testing $$s"; \
	  TEST_SVC_A="$$s-tests"; \
	  TEST_SVC_B="$$s-test"; \
	  if echo "$$ALL_SERVICES" | grep -qx "$$TEST_SVC_A"; then \
	    $(COMPOSE) run --rm $$TEST_SVC_A pytest -q || exit 1; \
	  elif echo "$$ALL_SERVICES" | grep -qx "$$TEST_SVC_B"; then \
	    $(COMPOSE) run --rm $$TEST_SVC_B pytest -q || exit 1; \
	  else \
	    $(COMPOSE) run --rm $$s pytest -q || exit 1; \
	  fi; \
	done

# Shortcut: make test-gateway (auto-uses gateway-tests if defined)
test-%:
	@set -e; \
	ALL_SERVICES="$$( $(COMPOSE) config --services )"; \
	SVC="$*"; \
	TEST_SVC_A="$$SVC-tests"; \
	TEST_SVC_B="$$SVC-test"; \
	if echo "$$ALL_SERVICES" | grep -qx "$$TEST_SVC_A"; then \
	  $(COMPOSE) run --rm $$TEST_SVC_A pytest -q; \
	elif echo "$$ALL_SERVICES" | grep -qx "$$TEST_SVC_B"; then \
	  $(COMPOSE) run --rm $$TEST_SVC_B pytest -q; \
	else \
	  $(COMPOSE) run --rm $$SVC pytest -q; \
	fi
