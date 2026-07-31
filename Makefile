# Makefile — luana-platform monorepo
# Wrappers Docker dev + CI parity + portfolio + infra management.
#
# S-DOCKER-DEV-MULTIBRAND T-6 — 2026-05-15
# Decisions: D2 (brand-autocontenida), D6 (port allocation cementada)
#
# Decisión 8 (Story 10 Phase 0 ratificada 2026-05-12):
# ci-parity location = luana-platform root (cross-brand pattern).
# Stories 11-13 (vitalia, comunify, lupulo) heredan automatico.

# ════════════════════════════════════════════════════════════════
# Workspace root (used by Phase 4b targets — schema v2 ledger + releases)
# ════════════════════════════════════════════════════════════════
WS := $(shell git rev-parse --show-toplevel)

# Python venv resolver: prefer worktree-local .venv, fallback a luana-platform principal
# (worktrees efímeros como protocol-* no tienen .venv propio)
PYTHON := $(shell test -x $(WS)/.venv/bin/python && echo $(WS)/.venv/bin/python || echo /home/chalreme/Proyectos/luana-platform/.venv/bin/python)

# ════════════════════════════════════════════════════════════════
# BRANDS — append future brand slugs as their migration stories close
# ════════════════════════════════════════════════════════════════
BRANDS := vitalia

.PHONY: dev-nicolify dev-vitalia dev-comunify dev-lupulo dev-which
.PHONY: dev-vitalia-admin dev-vitalia-admin-down
.PHONY: dev-nicolify-tunnel dev-vitalia-tunnel dev-comunify-tunnel dev-lupulo-tunnel
.PHONY: dev-app-vitalia lane-auth lane-auth-vitalia lane-auth-nicolify lane-auth-comunify
.PHONY: dev-all dev-all-vector dev-all-cache
.PHONY: dev-down-nicolify dev-down-vitalia dev-down-comunify dev-down-lupulo dev-down-all
.PHONY: dev-clean-nicolify dev-clean-vitalia dev-clean-comunify dev-clean-lupulo dev-clean-all
.PHONY: infra-matrix portfolio portfolio-check scan-promotables
.PHONY: ci-parity $(BRANDS:%=ci-parity-%) ci-parity-be ci-parity-fe
.PHONY: releases-vitalia capability-ledger-check migrate-vitalia-schema
.PHONY: install-hooks help sync-all sync-check promote-to-main

COMPOSE_BASE := docker compose -f docker-compose.dev.yml

# ── dev targets ──────────────────────────────────────────────────────────────
# dev-{brand} pre-condition: scripts/dev-lock-check.sh enforces D5 (max 1 stack docker per brand)
dev-nicolify:
	@bash scripts/dev-lock-check.sh nicolify
	$(COMPOSE_BASE) -f nicolify/docker-compose.dev.yml up -d

dev-vitalia:
	@bash scripts/dev-lock-check.sh vitalia
	$(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml up -d

dev-comunify:
	@bash scripts/dev-lock-check.sh comunify
	$(COMPOSE_BASE) -f comunify/docker-compose.dev.yml up -d

dev-lupulo:
	@bash scripts/dev-lock-check.sh lupulo
	$(COMPOSE_BASE) -f lupulo/docker-compose.dev.yml up -d

# dev-which: read-only — qué worktree sirve cada stack de marca (cazar mismatch)
dev-which:
	@bash scripts/dev-lock-check.sh --which

# ── cross-worktree sync (core/harness) ───────────────────────────────────────
# Doctrina HB-86: cambio compartido = commit aislado brand-free → promote-to-main
# (cherry-pick del SHA, NO squash del branch) → sync-all (FF en cada worktree).
sync-all:                ## Poné al día TODAS las worktrees wip/* con main (FF-safe)
	@bash scripts/git/sync-all.sh
sync-check:              ## Preview: cuánto está atrás de main cada worktree (read-only)
	@bash scripts/git/sync-all.sh --check
promote-to-main:         ## Lift un commit compartido a main: make promote-to-main SHA="<sha> [<sha2>]"
	@test -n "$(SHA)" || { echo 'Uso: make promote-to-main SHA="<sha> [<sha2> ...]"'; exit 1; }
	@bash scripts/git/promote-to-main.sh $(SHA)

# ── dev-active: trabajar en UNA marca, liberar la RAM de las otras ────────────
# RAM: cada dev server FE (el bundler) pesa ~1.7-2.5GB. Cuando trabajás en una
# sola marca, el dev-active detiene los FE de las demás (libera ~2.5GB c/u) y
# deja sus backends vivos (livianos, ~30MB) por si necesitás sus APIs.
# Uso: make dev-active BRAND=vitalia   (→ ~2.7GB total en vez de ~4.6GB)
# Para volver a las 3 en dev simultáneo: make dev-all
dev-active:
	@test -n "$(BRAND)" || { echo "Uso: make dev-active BRAND=<nicolify|vitalia|comunify|lupulo>"; exit 1; }
	@echo "→ dev-active: solo $(BRAND) en dev; deteniendo FE de las otras marcas para liberar RAM"
	@for b in nicolify vitalia comunify lupulo; do \
	  if [ "$$b" != "$(BRAND)" ]; then \
	    docker stop luana-dev-$${b}_frontend_dev-1 >/dev/null 2>&1 && echo "  ⏹  $${b} FE detenido" || true; \
	  fi; \
	done
	$(COMPOSE_BASE) -f $(BRAND)/docker-compose.dev.yml up -d
	@echo "✓ $(BRAND) en dev. FE de las otras marcas detenido (backends siguen vivos). make dev-all para volver a las 3."

# ── vitalia admin panel (Streamlit port 8502) ───────────────────────────────
# Requires VITALIA_ADMIN_PASSWORD in vitalia/.env.dev
# Access: http://127.0.0.1:8502
dev-vitalia-admin:
	@bash scripts/dev-lock-check.sh vitalia
	$(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml --profile admin up -d

dev-vitalia-admin-down:
	$(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml --profile admin stop vitalia_admin_dev

# ── tunnel targets (cloudflared profile) ────────────────────────────────────
dev-nicolify-tunnel:
	$(COMPOSE_BASE) -f nicolify/docker-compose.dev.yml --profile tunnel up -d

dev-vitalia-tunnel:
	$(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml --profile tunnel up -d

dev-comunify-tunnel:
	$(COMPOSE_BASE) -f comunify/docker-compose.dev.yml --profile tunnel up -d

dev-lupulo-tunnel:
	$(COMPOSE_BASE) -f lupulo/docker-compose.dev.yml --profile tunnel up -d

# ── dev-app verified (stack + tunnel + live-verify readiness) ────────────────
# Levanta stack + cloudflared y VERIFICA que dev-app.{brand}lat.com sirve la app
# real, dejando todo listo para verificación live. SSoT: .claude/rules/definition-of-done-live-verify.md
dev-app-vitalia:
	bash scripts/dev-app-up.sh vitalia

dev-app-%:
	bash scripts/dev-app-up.sh $*

# ── lane-auth: seed Chrome DevTools MCP lane profile with a Clerk session (HB-89) ────
# El perfil MCP de la lane (~/.cache/chrome-devtools-mcp/luana-<brand>-$LUANA_LANE) no tiene
# sesión Clerk → los writes autenticados redirigen a /sign-in. Corré esto UNA vez por lane
# (re-corré si >4h). SSoT: .claude/rules/definition-of-done-live-verify.md + HB-89.
lane-auth-vitalia:
	bash scripts/lane-auth.sh vitalia
lane-auth-nicolify:
	bash scripts/lane-auth.sh nicolify
lane-auth-comunify:
	bash scripts/lane-auth.sh comunify

lane-auth:                ## Seed lane MCP Clerk session: make lane-auth BRAND=<vitalia|nicolify|comunify> [FORCE=1]
	@test -n "$(BRAND)" || { echo "Uso: make lane-auth BRAND=<vitalia|nicolify|comunify> [FORCE=1]"; exit 1; }
	bash scripts/lane-auth.sh $(BRAND) $(if $(FORCE),--force,)

# ── all-brands targets ───────────────────────────────────────────────────────
dev-all:
	$(COMPOSE_BASE) \
		-f nicolify/docker-compose.dev.yml \
		-f vitalia/docker-compose.dev.yml \
		-f comunify/docker-compose.dev.yml \
		-f lupulo/docker-compose.dev.yml \
		up -d

dev-all-vector:
	$(COMPOSE_BASE) \
		-f nicolify/docker-compose.dev.yml \
		-f vitalia/docker-compose.dev.yml \
		-f comunify/docker-compose.dev.yml \
		-f lupulo/docker-compose.dev.yml \
		--profile vector up -d

dev-all-cache:
	$(COMPOSE_BASE) \
		-f nicolify/docker-compose.dev.yml \
		-f vitalia/docker-compose.dev.yml \
		-f comunify/docker-compose.dev.yml \
		-f lupulo/docker-compose.dev.yml \
		--profile cache up -d

# ── down targets ─────────────────────────────────────────────────────────────
dev-down-nicolify:
	$(COMPOSE_BASE) -f nicolify/docker-compose.dev.yml down

dev-down-vitalia:
	$(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml down

dev-down-comunify:
	$(COMPOSE_BASE) -f comunify/docker-compose.dev.yml down

dev-down-lupulo:
	$(COMPOSE_BASE) -f lupulo/docker-compose.dev.yml down

dev-down-all:
	$(COMPOSE_BASE) \
		-f nicolify/docker-compose.dev.yml \
		-f vitalia/docker-compose.dev.yml \
		-f comunify/docker-compose.dev.yml \
		-f lupulo/docker-compose.dev.yml \
		down

# ── clean targets (volumes incluidos) ───────────────────────────────────────
dev-clean-nicolify:
	$(COMPOSE_BASE) -f nicolify/docker-compose.dev.yml down -v --remove-orphans

dev-clean-vitalia:
	$(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml down -v --remove-orphans

dev-clean-comunify:
	$(COMPOSE_BASE) -f comunify/docker-compose.dev.yml down -v --remove-orphans

dev-clean-lupulo:
	$(COMPOSE_BASE) -f lupulo/docker-compose.dev.yml down -v --remove-orphans

dev-clean-all:
	$(COMPOSE_BASE) \
		-f nicolify/docker-compose.dev.yml \
		-f vitalia/docker-compose.dev.yml \
		-f comunify/docker-compose.dev.yml \
		-f lupulo/docker-compose.dev.yml \
		down -v --remove-orphans

# ── infra management ─────────────────────────────────────────────────────────
infra-matrix:
	.venv/bin/python scripts/generate_infra_matrix.py

# ════════════════════════════════════════════════════════════════
# Portfolio + promotion scan (multibrand SSoT auto-gen)
# ════════════════════════════════════════════════════════════════
portfolio:
	python3 scripts/generate_portfolio.py

portfolio-check:
	python3 scripts/generate_portfolio.py --check

scan-promotables:
	python3 scripts/scan_promotables.py

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
# Uso: make code-health BRAND=vitalia [SURFACE=be|fe|all]  ·  --update-baseline: make code-health-baseline BRAND=x
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

capability-index-all:
	python3 scripts/generate_capability_index.py --all-brands

# v3 cement 2026-05-27 · ADR-vitalia-005 · SYSTEM-MAP cross-vocabulary validation
system-map-validate:
	python3 scripts/validate_system_map.py --brand vitalia

system-map-validate-all:
	python3 scripts/validate_system_map.py --all-brands

# ════════════════════════════════════════════════════════════════
# HB-51 · cap-format enforcement determinístico (8 capas)
# ════════════════════════════════════════════════════════════════
new-cap:  ## Generar una cap schema-válida (Capa 2). Uso: make new-cap BRAND=vitalia MODULE=inbox SLUG=adrian-inbox [AREA=adrian.inbox] [AGENT=adrian] [NAME="..."] [STORY=...]
	@test -n "$(BRAND)" || (echo "BRAND= requerido (ej: vitalia)"; exit 1)
	@test -n "$(MODULE)" || (echo "MODULE= requerido (tech_module dir)"; exit 1)
	@test -n "$(SLUG)" || (echo "SLUG= requerido (kebab)"; exit 1)
	$(PYTHON) scripts/new_cap.py --brand $(BRAND) --module $(MODULE) --slug $(SLUG) \
		--agent "$(or $(AGENT),TODO-agent)" --area "$(AREA)" --name "$(NAME)" --story "$(or $(STORY),TBD)"

caps-schema-check:  ## Capa 3 · validar schema de las caps (advisory). BRAND= o todas
	$(PYTHON) scripts/validate_caps_schema.py $(if $(BRAND),--brand $(BRAND),--all-brands)

cap-gates:  ## Capa 4 · correr G1-G6 sobre un brand. BRAND= (default vitalia)
	$(PYTHON) scripts/validate_code_cap_bidirectional.py --brand $(or $(BRAND),vitalia)

cap-doctor:  ## Capa 8 · health report code↔cap de un vistazo (orphan headers · cajas vacías · paths rotos · supersesiones). BRAND= o todas
	$(PYTHON) scripts/cap_doctor.py $(if $(BRAND),--brand $(BRAND),--all-brands)

# ════════════════════════════════════════════════════════════════
# CI parity gate (cross-brand)
# ════════════════════════════════════════════════════════════════
ci-parity: $(BRANDS:%=ci-parity-%)
	@printf "\033[32mci-parity all brands GREEN: $(BRANDS)\033[0m\n"

ci-parity-%: scripts/ci-parity.sh
	@printf "\033[34m-- Running ci-parity for brand: $* --\033[0m\n"
	bash scripts/ci-parity.sh --brand=$*

ci-parity-be:
	@for brand in $(BRANDS); do \
		bash scripts/ci-parity.sh --brand=$$brand --skip-fe; \
	done

ci-parity-fe:
	@for brand in $(BRANDS); do \
		bash scripts/ci-parity.sh --brand=$$brand --skip-be; \
	done

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

capability-ledger-check:  ## Run reconcile --validate-ledger across all active brands
	@for b in vitalia nicolify comunify lupulo; do \
		echo "=== $$b cap ledger check ==="; \
		$(PYTHON) scripts/reconcile_capabilities.py --brand $$b --validate-ledger || exit 1; \
	done

migrate-vitalia-schema:  ## One-shot · migrate vitalia to schema v2 (releases + cap ledger) · idempotent
	$(PYTHON) scripts/migrate_to_release_schema.py --brand vitalia
	$(PYTHON) scripts/migrate_capability_ledger.py --brand vitalia

# ════════════════════════════════════════════════════════════════
# Cockpit: el launcher (cockpit-daemon.sh) MIGRÓ a chris-corp (home base, I-48).
# El multi-cockpit es la vista del DUEÑO → se prende desde chris-corp (modo único = multi · :4000):
#   make -C ~/Proyectos/chris-corp cockpit-up
# Binario = prenter-harness/products/cockpit-go; registry = ~/.cockpit/cockpit.yaml.
# ════════════════════════════════════════════════════════════════

# ── hooks ────────────────────────────────────────────────────────────────────
# D2 (W7, 2026-06-09): source-DETERMINISTIC. The shared .git/hooks/ (common-git-dir) must
# resolve from a STABLE canonical worktree, NOT $TOP (the invoking worktree → last-writer-wins
# across worktrees). Canonical = the MAIN worktree (parent of --git-common-dir). DIP: a shared
# resource depends on a stable source. Cadence: hook edits land on wip/* → merge to main →
# main IS the canonical running gate ("main lags" is a merge step, not a coupling to dodge).
install-hooks:
	@HOOKS_DIR="$$(git rev-parse --git-path hooks)"; \
	 GIT_COMMON="$$(cd "$$(git rev-parse --git-common-dir)" && pwd)"; \
	 CANONICAL="$$(dirname "$$GIT_COMMON")"; \
	 mkdir -p "$$HOOKS_DIR"; \
	 ln -sf "$$CANONICAL/scripts/git-hooks/pre-commit" "$$HOOKS_DIR/pre-commit"; \
	 [ -f "$$CANONICAL/scripts/git-hooks/pre-push" ] && ln -sf "$$CANONICAL/scripts/git-hooks/pre-push" "$$HOOKS_DIR/pre-push" || true; \
	 [ -f "$$CANONICAL/scripts/git-hooks/post-commit" ] && ln -sf "$$CANONICAL/scripts/git-hooks/post-commit" "$$HOOKS_DIR/post-commit" || true; \
	 echo "git hooks installed to $$HOOKS_DIR from canonical worktree $$CANONICAL (deterministic · D2)"

# ── help ─────────────────────────────────────────────────────────────────────
help:
	@echo "luana-platform Makefile targets:"
	@echo ""
	@echo "  Dev environment:"
	@echo "  make dev-{brand}              Start {brand} dev environment (brand=nicolify|vitalia|comunify|lupulo)"
	@echo "  make dev-which                Show which worktree each running brand stack binds (cazar mismatch)"
	@echo "  make sync-all                 Put ALL wip/* worktrees up-to-date with main (FF-safe)"
	@echo "  make sync-check               Preview how far behind main each worktree is (read-only)"
	@echo "  make promote-to-main SHA=...  Lift a shared (core/harness) commit to main via cherry-pick"
	@echo "  make dev-{brand}-tunnel       Start {brand} + cloudflared tunnel (profile=tunnel)"
	@echo "  make dev-app-vitalia          Start stack + tunnel + VERIFY dev-app ready for live-verify"
	@echo "  make dev-all                  Start all 4 brands simultaneously"
	@echo "  make dev-all-vector           Start all brands + qdrant (profile=vector)"
	@echo "  make dev-all-cache            Start all brands + redis (profile=cache)"
	@echo "  make dev-down-{brand}         Stop {brand} containers"
	@echo "  make dev-down-all             Stop all brand containers"
	@echo "  make dev-clean-{brand}        Stop + remove volumes for {brand}"
	@echo "  make dev-clean-all            Stop + remove all volumes"
	@echo ""
	@echo "  Infra management:"
	@echo "  make infra-matrix             Regenerate docs/portfolio/INFRA-MATRIX.md"
	@echo ""
	@echo "  Portfolio + promotables:"
	@echo "  make portfolio                Regen docs/portfolio/ (11 universos)"
	@echo "  make portfolio-check          Check portfolio fresh (exit 1 if stale)"
	@echo "  make scan-promotables         Scan brand learnings for cross-brand patterns"
	@echo ""
	@echo "  CI parity:"
	@echo "  make ci-parity                Run CI parity sweep ALL brands ($(BRANDS))"
	@echo "  make ci-parity-{brand}        Run CI parity sweep for specific brand"
	@echo ""
	@echo "  Hooks:"
	@echo "  make install-hooks            Install git hooks (pre-commit)"
	@echo ""
	@echo "Brands enabled: $(BRANDS)"
	@echo "Postgres shared: 127.0.0.1:5435"
	@echo "Ports: nicolify=8001/3001, vitalia=8002/3002, comunify=8003/3003, lupulo=8004/3004"

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
