# Makefile — vitalia-app (repo standalone single-brand)
# Wrappers Docker dev + CI parity + infra management + cockpit.
#
# Origen: luana-platform monorepo (S-DOCKER-DEV-MULTIBRAND 2026-05-15).
# Cirugía single-brand 2026-07-31: solo existe la marca vitalia; los targets
# de marcas fantasma (nicolify/comunify/lupulo) y la machinery de worktrees
# (sync-all/sync-check) fueron retirados.

# ════════════════════════════════════════════════════════════════
# Workspace root
# ════════════════════════════════════════════════════════════════
WS := $(shell git rev-parse --show-toplevel)

# Python venv resolver: workspace-root .venv, fallback python3 del sistema
PYTHON := $(shell test -x $(WS)/.venv/bin/python && echo $(WS)/.venv/bin/python || echo python3)

# ════════════════════════════════════════════════════════════════
# BRANDS — single-brand: vitalia
# ════════════════════════════════════════════════════════════════
BRANDS := vitalia

.PHONY: dev-vitalia dev-all dev-active dev-which
.PHONY: dev-vitalia-admin dev-vitalia-admin-down
.PHONY: dev-vitalia-tunnel dev-app-vitalia lane-auth lane-auth-vitalia litellm-up litellm-down litellm-status
.PHONY: dev-vitalia-vector dev-vitalia-cache
.PHONY: dev-down-vitalia dev-down-all dev-clean-vitalia dev-clean-all

.PHONY: ci-parity $(BRANDS:%=ci-parity-%) ci-parity-be ci-parity-fe
.PHONY: releases-vitalia capability-ledger-check migrate-vitalia-schema
.PHONY: install-hooks help

COMPOSE_BASE := docker compose -f docker-compose.dev.yml

# ── dev targets ──────────────────────────────────────────────────────────────
# dev-vitalia pre-condition: scripts/dev-lock-check.sh enforces max 1 stack docker
dev-vitalia:
	@bash scripts/dev-lock-check.sh vitalia
	$(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml up -d

# dev-all: alias retro-compat (docs/skills citan `make dev-all`) — single-brand = dev-vitalia
dev-all: dev-vitalia

# dev-active: alias retro-compat — con una sola marca no hay FE ajeno que detener
dev-active: dev-vitalia

# dev-which: read-only — qué stack corre y desde dónde
dev-which:
	@bash scripts/dev-lock-check.sh --which

# ── main promotion (commit compartido core/harness desde wip/*) ──────────────
# ── vitalia admin panel (Streamlit port 8502) ───────────────────────────────
# Requires VITALIA_ADMIN_PASSWORD in vitalia/.env.dev
# Access: http://127.0.0.1:8502
dev-vitalia-admin:
	@bash scripts/dev-lock-check.sh vitalia
	$(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml --profile admin up -d

dev-vitalia-admin-down:
	$(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml --profile admin stop vitalia_admin_dev

# ── tunnel target (cloudflared profile) ─────────────────────────────────────
dev-vitalia-tunnel:
	$(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml --profile tunnel up -d

# ── dev-app verified (stack + tunnel + live-verify readiness) ────────────────
# Levanta stack + cloudflared y VERIFICA que dev-app.vitalialat.com sirve la app
# real, dejando todo listo para verificación live. SSoT: .claude/rules/definition-of-done-live-verify.md
dev-app-vitalia:
	bash scripts/dev-app-up.sh vitalia

# ── LiteLLM proxy (gateway LLM dev — requerido para cualquier llamada LLM) ──
# Keys: deploy/litellm/.env (copiar de deploy/litellm/.env.example, gitignored).
# Config: deploy/litellm/config.dev.yaml (tracked). Puerto 4000.
litellm-up:
	bash scripts/litellm-proxy-up.sh

litellm-down:
	docker rm -f luana_litellm_dev 2>/dev/null || true
	@echo "✓ litellm proxy down"

litellm-status:
	@docker ps --filter name=luana_litellm_dev --format '{{.Names}}  {{.Status}}' | grep . \
		|| echo "✗ luana_litellm_dev DOWN (make litellm-up)"

# ── lane-auth: seed Chrome DevTools MCP lane profile with a Clerk session (HB-89) ────
# El perfil MCP de la lane no tiene sesión Clerk → los writes autenticados redirigen
# a /sign-in. Corré esto UNA vez por lane (re-corré si >4h).
# SSoT: .claude/rules/definition-of-done-live-verify.md + HB-89.
lane-auth-vitalia:
	bash scripts/lane-auth.sh vitalia

lane-auth:                ## Seed lane MCP Clerk session: make lane-auth [FORCE=1]
	bash scripts/lane-auth.sh vitalia $(if $(FORCE),--force,)

# ── profile targets (qdrant / redis) ─────────────────────────────────────────
dev-vitalia-vector:
	$(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml --profile vector up -d

dev-vitalia-cache:
	$(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml --profile cache up -d

# ── down targets ─────────────────────────────────────────────────────────────
dev-down-vitalia:
	$(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml down

dev-down-all: dev-down-vitalia

# ── clean targets (volumes incluidos) ───────────────────────────────────────
dev-clean-vitalia:
	$(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml down -v --remove-orphans

dev-clean-all: dev-clean-vitalia

# ── infra management ─────────────────────────────────────────────────────────
docs-graph:  ## Grafo de consumo root docs/ + manifest vivos (DOCS-SWEEP 2026-06-10 · reporte gitignored docs/process/DOCS-GRAPH.md)
	python3 scripts/scan_docs_graph.py --manifest

extraction-contract:  ## Regenera core/luana-core-analytics-engine/docs/extraction-contract.md (ETL SSoT · target restaurado 2026-06-09, lo citan AGENTS.md + etl rule + metrics-expert)
	$(PYTHON) core/luana-core-analytics-engine/scripts/generate_extraction_contract_doc.py

# ADR-016 · C2-T1: catálogo @luana/ui-kit (GITIGNORED — auto-gen R3)
# Cruza src/index.ts + storybook-static/index.json → catalog.json + catalog.md
.PHONY: ui-catalog
ui-catalog:  ## Regenera core/@luana/ui-kit/catalog.json + catalog.md (inventario SSoT · ADR-016 C2-T1)
	node scripts/generate_ui_catalog.mjs

# Storybook del design system (@luana/ui-kit) = SSoT visual (canon §5 · ADR-016)
# corepack pnpm (no el shim de PATH) → corre aunque make spawnee un shell sin pnpm en PATH
.PHONY: storybook
storybook:  ## Levanta el Storybook del DS (@luana/ui-kit) en http://localhost:6007
	corepack pnpm --filter @luana/ui-kit storybook

# machinery hardening anti-drift (auditoría 2026-05-28) — doctrina↔templates↔agentes consistentes
machinery-check:
	python3 scripts/validate_machinery_consistency.py

# model tiers (pedido Chris 2026-06-12) — frontmatter `model:` = generado desde project.config.yaml::models.
# Swap de modelo = 1 línea en el seam + `make models-sync`. Drift bloqueado por machinery CHECK 31.
.PHONY: models-sync models-check
models-sync:                     ## Parchea frontmatter model: de agents/skills desde el seam
	python3 scripts/sync_model_tiers.py --write
models-check:                    ## Verifica frontmatter model: == seam (exit 1 si drift)
	python3 scripts/sync_model_tiers.py --check

# anti-rot de punteros del harness (HB · 2026-06-08) — refs workspace-rooted rotos en skills/agents/rules.
# Advisory + baseline-ratchet shrink-only. Surfaceado por machinery CHECK 28 + /harnesses-improvement.
.PHONY: harness-pointers harness-pointers-baseline
harness-pointers:                ## Reporta punteros rotos NUEVOS vs baseline (--all para ver todos)
	python3 scripts/scan_harness_pointers.py --all
harness-pointers-baseline:       ## Congela el scan actual como baseline (tras drenar/arreglar refs)
	python3 scripts/scan_harness_pointers.py --update-baseline

# code-health gate (HB-61 · 2026-06-08) — mantenibilidad BE+FE: dead-code + dup + docstrings + vuln, baseline-ratchet.
# Uso: make code-health [SURFACE=be|fe|all]  ·  --update-baseline: make code-health-baseline
.PHONY: code-health code-health-baseline
code-health:
	bash scripts/quality/code-health.sh $(or $(BRAND),vitalia) $(or $(SURFACE),all)

code-health-baseline:
	bash scripts/quality/code-health.sh $(or $(BRAND),vitalia) $(or $(SURFACE),all) --update-baseline

# v3 cement 2026-05-27 · ADR-vitalia-005 · capability index user-facing
capability-index:
	python3 scripts/generate_capability_index.py --brand vitalia

capability-index-check:
	python3 scripts/generate_capability_index.py --brand vitalia --check

# v3 cement 2026-05-27 · ADR-vitalia-005 · SYSTEM-MAP cross-vocabulary validation
system-map-validate:
	python3 scripts/validate_system_map.py --brand vitalia

# ════════════════════════════════════════════════════════════════
# HB-51 · cap-format enforcement determinístico (8 capas)
# ════════════════════════════════════════════════════════════════
new-cap:  ## Generar una cap schema-válida (Capa 2). Uso: make new-cap MODULE=inbox SLUG=adrian-inbox [AREA=adrian.inbox] [AGENT=adrian] [NAME="..."] [STORY=...]
	@test -n "$(MODULE)" || (echo "MODULE= requerido (tech_module dir)"; exit 1)
	@test -n "$(SLUG)" || (echo "SLUG= requerido (kebab)"; exit 1)
	$(PYTHON) scripts/new_cap.py --brand vitalia --module $(MODULE) --slug $(SLUG) \
		--agent "$(or $(AGENT),TODO-agent)" --area "$(AREA)" --name "$(NAME)" --story "$(or $(STORY),TBD)"

caps-schema-check:  ## Capa 3 · validar schema de las caps (advisory)
	$(PYTHON) scripts/validate_caps_schema.py --brand vitalia

cap-gates:  ## Capa 4 · correr G1-G6 sobre vitalia
	$(PYTHON) scripts/validate_code_cap_bidirectional.py --brand vitalia

cap-doctor:  ## Capa 8 · health report code↔cap de un vistazo (orphan headers · cajas vacías · paths rotos · supersesiones)
	$(PYTHON) scripts/cap_doctor.py --brand vitalia

# ════════════════════════════════════════════════════════════════
# CI parity gate
# ════════════════════════════════════════════════════════════════
ci-parity: $(BRANDS:%=ci-parity-%)
	@printf "\033[32mci-parity GREEN: $(BRANDS)\033[0m\n"

ci-parity-%: scripts/ci-parity.sh
	@printf "\033[34m-- Running ci-parity for brand: $* --\033[0m\n"
	bash scripts/ci-parity.sh --brand=$*

ci-parity-be:
	bash scripts/ci-parity.sh --brand=vitalia --skip-fe

ci-parity-fe:
	bash scripts/ci-parity.sh --brand=vitalia --skip-be

# ════════════════════════════════════════════════════════════════
# Phase 4b — Release schema v2 + capability ledger (cement 2026-05-27)
# ════════════════════════════════════════════════════════════════

releases-vitalia:  ## Generate BACKLOG by release for vitalia + show stats
	$(PYTHON) scripts/generate_backlog.py --brand vitalia
	@echo ""
	@echo "=== Vitalia releases status ==="
	@for f in vitalia/docs/product/releases/F*.yaml; do \
		release_id=$$(basename $$f .yaml); \
		status=$$(grep -E "^status:" $$f | awk '{print $$2}'); \
		stories_count=$$(grep -cE "^  - " $$f || echo 0); \
		echo "$$release_id · status=$$status · stories=$$stories_count"; \
	done

capability-ledger-check:  ## Run reconcile --validate-ledger (vitalia)
	@echo "=== vitalia cap ledger check ==="
	$(PYTHON) scripts/reconcile_capabilities.py --brand vitalia --validate-ledger

migrate-vitalia-schema:  ## One-shot · migrate vitalia to schema v2 (releases + cap ledger) · idempotent
	$(PYTHON) scripts/migrate_to_release_schema.py --brand vitalia
	$(PYTHON) scripts/migrate_capability_ledger.py --brand vitalia

# ── hooks ────────────────────────────────────────────────────────────────────
# Source-deterministic: los hooks compartidos de .git/hooks se symlinkan desde el
# worktree canónico (= este repo único). Cadence: hook edits land on wip/* →
# merge to main → main IS the canonical running gate.
install-hooks:
	@HOOKS_DIR="$$(git rev-parse --git-path hooks)"; \
	 GIT_COMMON="$$(cd "$$(git rev-parse --git-common-dir)" && pwd)"; \
	 CANONICAL="$$(dirname "$$GIT_COMMON")"; \
	 mkdir -p "$$HOOKS_DIR"; \
	 ln -sf "$$CANONICAL/scripts/git-hooks/pre-commit" "$$HOOKS_DIR/pre-commit"; \
	 [ -f "$$CANONICAL/scripts/git-hooks/pre-push" ] && ln -sf "$$CANONICAL/scripts/git-hooks/pre-push" "$$HOOKS_DIR/pre-push" || true; \
	 echo "git hooks installed to $$HOOKS_DIR from $$CANONICAL"

# ── help ─────────────────────────────────────────────────────────────────────
help:
	@echo "vitalia-app Makefile targets:"
	@echo ""
	@echo "  Dev environment:"
	@echo "  make dev-vitalia              Start vitalia dev environment (alias: dev-all, dev-active)"
	@echo "  make dev-which                Show which dir serves the running stack (cazar mismatch)"
	@echo "  make dev-vitalia-tunnel       Start vitalia + cloudflared tunnel (profile=tunnel)"
	@echo "  make dev-app-vitalia          Start stack + tunnel + VERIFY dev-app ready for live-verify"
	@echo "  make dev-vitalia-vector       Start vitalia + qdrant (profile=vector)"
	@echo "  make dev-vitalia-cache        Start vitalia + redis (profile=cache)"
	@echo "  make dev-vitalia-admin        Start vitalia admin panel (Streamlit :8502)"
	@echo "  make dev-down-vitalia         Stop vitalia containers (alias: dev-down-all)"
	@echo "  make dev-clean-vitalia        Stop + remove volumes (alias: dev-clean-all)"
	@echo "  make lane-auth                Seed lane MCP Clerk session [FORCE=1]"
	@echo "  make litellm-up               Proxy LLM dev (:4000) — keys en deploy/litellm/.env"
	@echo "  make litellm-status           Proxy LLM: estado"
	@echo ""
	@echo "  Git:"
	@echo "  make install-hooks            Install git hooks (pre-commit, pre-push)"
	@echo ""
	@echo "  CI parity:"
	@echo "  make ci-parity                Run CI parity sweep (vitalia)"
	@echo "  make ci-parity-be / -fe       Backend-only / frontend-only sweep"
	@echo ""
	@echo "  Capabilities + docs:"
	@echo "  make cap-doctor               Health report code↔cap"
	@echo "  make cap-gates                Gates G1-G6 (vitalia)"
	@echo "  make new-cap MODULE=.. SLUG=..  Generate schema-valid cap"
	@echo "  make releases-vitalia         BACKLOG by release + stats"
	@echo "  make machinery-check          Doctrine↔templates↔agents consistency"
	@echo "  make models-check / -sync     Model tier frontmatter vs seam"
	@echo ""
	@echo "  Cockpit:"
	@echo "  make cockpit-up / -down / -status / -build   Cockpit SDD vendored (:$(COCKPIT_PORT))"
	@echo ""
	@echo "Brand: vitalia (single-brand standalone)"
	@echo "Postgres: 127.0.0.1:5435 · Backend: :8002 · Frontend: :3002 · Cockpit: :$(COCKPIT_PORT)"

# ── Cockpit SDD vendored (tools/cockpit · extraído de prenter-harness products/devhub) ──
COCKPIT_BIN  := tools/cockpit/go/cockpit
COCKPIT_PORT := 4002

.PHONY: cockpit-up cockpit-down cockpit-status cockpit-build

cockpit-up: ## Prende el cockpit SDD leyendo ESTE workspace (:4002 · sobrevive cierre de terminal)
	@mkdir -p .cockpit-local
	@if [ -f .cockpit-local/cockpit.pid ] && kill -0 $$(cat .cockpit-local/cockpit.pid) 2>/dev/null; then \
		echo "cockpit ya corre (pid $$(cat .cockpit-local/cockpit.pid)) → http://localhost:$(COCKPIT_PORT)"; \
	else \
		setsid nohup $(COCKPIT_BIN) start -workspace $(CURDIR) -port $(COCKPIT_PORT) > .cockpit-local/cockpit.log 2>&1 & \
		echo $$! > .cockpit-local/cockpit.pid; \
		sleep 1; echo "cockpit up (pid $$(cat .cockpit-local/cockpit.pid)) → http://localhost:$(COCKPIT_PORT)"; \
	fi

cockpit-down: ## Baja el cockpit
	@[ -f .cockpit-local/cockpit.pid ] && kill $$(cat .cockpit-local/cockpit.pid) 2>/dev/null && rm -f .cockpit-local/cockpit.pid && echo "cockpit down" || echo "cockpit no corre"

cockpit-status: ## Estado del cockpit
	@[ -f .cockpit-local/cockpit.pid ] && kill -0 $$(cat .cockpit-local/cockpit.pid) 2>/dev/null && echo "UP pid $$(cat .cockpit-local/cockpit.pid) → http://localhost:$(COCKPIT_PORT)" || echo "DOWN"

cockpit-build: ## Rebuild binario (UI estática + go build) — requiere go + pnpm
	cd tools/cockpit/ui && pnpm install --ignore-workspace
	cd tools/cockpit/go && ./build.sh
	cd tools/cockpit/sidecar && npm install && npm run build
