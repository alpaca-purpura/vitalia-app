# Merge artifact — vitalia/vitalia-fase1-stack-stability

> Brand: vitalia
> Story: F1-S0 vitalia-fase1-stack-stability (blocker hard Fase 1)
> Merged at: 2026-05-23T01:35:00-05:00
> Branch wip/vitalia commits: 16d7bd1d (ready package) · 64b6c2f7 (claim) · c1690216 · 7fa38b41 · 72592a2d · 9a9a8165 · 52bbc3f6 · d6cc6592 · 4f3c5d6b (developed) · a29ae24a (audit ESCALATED) · 1a296b56 (fixes #1-4) · 2d105e7e (fixes #5-6 + goldens)
> Audit verdict: APPROVED (Chris ratify 2026-05-23T01:30 post 6 fixes in-loop)

## § 1 — Gherkin verification matrix

> Copia exacta de `06-audit/gherkin-matrix.md` post in-loop fix session.

| Scenario (01-spec.md § 6) | Test path / validator | Status |
|---|---|---|
| Scenario 1 — happy-path full pipeline | `fe_typecheck` + `fe_lint` + `fe_vitest_existing_regression` + `visual_shadcn_primitives_{light,dark}` + `visual_agent_tokens_swatch_{light,dark}` | ✅ PASS |
| Scenario 2 — negative Tailwind v4 roto | `fe_build_production` + `visual_dashboard_legacy_{light,dark}` | ✅ PASS post Fix #5 (Tailwind v4 PostCSS setup) |
| Scenario 3 — Shadcn primitive render | `visual_shadcn_primitives_{light,dark}` | ✅ PASS |
| Scenario 4 — agent tokens + dark structural | `fe_agent_tokens_css_vars_grep` + `fe_tailwind_agent_colors_resolvable_introspection` + `visual_agent_tokens_swatch_{light,dark}` | ✅ PASS |
| Scenario 5 — Shadcn install partial failure | `fe_components_json_present` + `fe_8_primitives_present_ls` | ✅ PASS |
| Scenario 6 — build error post-install | `fe_build_production` | ✅ PASS post Fix #4 (marketing-nuqs-ssr-fix) |
| Scenario 7 — adversarial-declared (supply-chain) | ADR-vitalia-002 § 7 post-install audit checklist + /auditor PR review manual | ✅ N/A documented |
| Scenario 8 — not_applicable_batch (9 sub-categorías) | race_condition, concurrent_users, network_failure, empty_state, large_dataset, accessibility_keyboard, mobile_responsive, loading_state, i18n | ✅ N/A documented |

**Resultado**: 6 scenarios funcionales PASS + 2 N/A documented = 8/8 cubiertos.

## § 2 — Playwright E2E run

Última corrida targeted a F1-S0 visual baseline (2026-05-23T01:25):

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend
E2E_BASE_URL=http://localhost:3002 npx playwright test \
  --project=visual --grep "stack-stability" --update-snapshots
```

Verdict:
- Tests run: 8 (1 setup + 6 visual goldens + 1 cleanup)
- Passed: 8
- Failed: 0
- Duration: 6.2s
- Output: 6 PNG goldens en `vitalia/frontend/e2e/__screenshots__/visual/stack-stability/dev-stack-baseline.spec.ts/`

Goldens ratificados Chris visualmente vs Design Contract § 5.1 + agentes thumbnails canónicos `/home/chalreme/Trabajo/Vitalia/agentes/`.

Ratchet shrink-only desde 2026-05-23 — cualquier diff > 0.001 en re-run requiere re-ratify Chris explícito.

## § 3 — Capabilities updated/created

NEW:
- `vitalia/docs/product/capabilities/platform/shell-foundation-shadcn-tailwind-v4.yaml` (status: live, version 0.1.0)

Esta capability acopla 8 surfaces (Tailwind v4 + PostCSS infra · 8 Shadcn primitivos · 7 agent tokens CSS · Agent SSoT TS · Agent imagery · Test pages preview · Playwright visual project · 6 visual goldens · Arch fitness no-vt-classes · ADR-002 deprecation plan).

UPDATE: ninguna (F1-S0 es foundation story, no extiende capabilities pre-existentes — sólo establece nueva).

## § 4 — Modules MD refreshed

- `vitalia/docs/product/modules/platform.md` (auto-list refresh post-merge) — appended `shell-foundation-shadcn-tailwind-v4` en sección "Capabilities live".

Comando regen:
```bash
WS=$(git rev-parse --show-toplevel)
${WS}/.venv/bin/python ${WS}/scripts/reconcile_capabilities.py --brand vitalia --refresh-modules
```

## § 5 — How to verify (reproducible commands)

```bash
WS=$(git rev-parse --show-toplevel)

# 0. Stack levantado (post merge a main + checkout)
cd ${WS} && make dev-vitalia
# Esperar ~30s. Verificar containers:
#   docker ps --filter "name=vitalia" --format "table {{.Names}}\t{{.Status}}"
# Esperado: 3 containers UP (frontend :3002, backend :8002, cloudflared tunnel)

# 1. TypeScript strict (cero errores)
cd ${WS}/vitalia/frontend && npx tsc --noEmit
# Exit 0

# 2. ESLint (cero errores con --max-warnings 0)
cd ${WS}/vitalia/frontend && npx eslint src/ --cache --max-warnings 0
# Exit 0

# 3. Prettier format check
cd ${WS}/vitalia/frontend && npx prettier --check src/
# Exit 0

# 4. Vitest unit + integration + arch fitness
cd ${WS}/vitalia/frontend && npx vitest run --reporter=default
# Expected: 101 test files passed (740 tests), Duration ~5.8s, coverage > 20% thresholds
# Incluye: src/__tests__/architecture/test-no-vt-classes-in-new-features.test.ts GREEN

# 5. Production build (catch CSS vars + SSR issues)
cd ${WS}/vitalia/frontend && npm run build
# Exit 0 (post Fix #4 marketing-nuqs-ssr-fix con "use client" directive)

# 6. Visual goldens regression (re-run sin --update-snapshots)
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test --project=visual --grep "stack-stability"
# Expected: 8/8 PASS (maxDiffPixelRatio < 0.001 vs commited goldens)

# 7. Live preview pages
curl -s -o /dev/null -w "primitives: %{http_code}\n" \
  http://localhost:3002/test-stack/primitives
curl -s -o /dev/null -w "agent-tokens: %{http_code}\n" \
  http://localhost:3002/test-stack/agent-tokens
# Expected: 200 + 200

# 8. Backend health (post migration 024b NPS table)
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8002/health
# Expected: 200

# 9. Alembic chain verified
docker exec luana-dev-vitalia_backend_dev-1 bash -c \
  "cd /workspace && /workspace/.venv/bin/alembic -c vitalia/backend/alembic.ini history" \
  | head -15
# Expected: 001_vitalia → 024_vitalia → 024b_vitalia → 025_vitalia → 026..031_vitalia (no breaks)

# 10. Components.json + 8 primitives present
cd ${WS}/vitalia/frontend && test -f components.json && ls src/components/ui/ | wc -l
# Expected: returns 0 + "8" (avatar, badge, button, dropdown-menu, input, tabs, textarea, tooltip)

# 11. Agent SSoT consumable
cd ${WS}/vitalia/frontend && node -e "import('./src/lib/agents.ts').then(m => console.log(Object.keys(m.AGENTS)))" \
  2>/dev/null || echo "SSoT requires tsx/ts-node — verify via grep instead:" && \
  grep -c "AGENTS\." src/lib/agents.ts
# Expected: 6 agent slugs OR ≥6 references

# 12. ADR-vitalia-002 8 secciones presentes
test $(grep -cE "^## § [1-8]" ${WS}/vitalia/docs/architecture/ADR-vitalia-002-vt-deprecation-plan.md) -ge 8 && echo "OK"
# Expected: OK
```

**Expected**: todos los comandos exit 0 / 200 / OK.
