<!-- voseo-allowed: guidelines internas de migración, no user-facing -->
# 05-guidelines — vitalia-paradigm-map-zones

## Patterns required

### BE / scripts / docs (builder-backend)
- Scripts Python idempotentes con `--dry-run` (default seguro) y `--apply`. Usar `${WS}/.venv/bin/python`.
- Migración de caps consume `SYSTEM-MAP zones[].target_boxes[].absorbs` como tabla de verdad mecánica — NO hardcodear mapeos en el script (leerlos del YAML).
- **HALT-no-silent**: si una cap no matchea ninguna `absorbs`, imprimir lista + `exit 1`. NUNCA caja por defecto.
- `git mv` para renames de stories/dirs (preserva historia). Commit por pathspec (`git commit <rutas>`, índice compartido hub — ver git-haiku-delegation.md).
- Deprecar, no remover: `config`/`infra` en `agents[]` → `status: deprecated` (preserva trazabilidad histórica).
- Actions-index = **compositor** sobre `_code-index.json` (ya existe) + `dev_preview` de caps. NO grep-walker nuevo.
- Cap nuevo `platform/product-map-zonas.yaml`: schema v4 completo + `change_log[0].type: new` + `map_box: plataforma-tecnica` + `user_visible: false`.

### FE shell (builder-frontend)
- `agent-catalog.ts` es el SSoT — cambiar PRIMERO, propagar (Ribbon/routing/SubTabs derivan de él).
- Migrar catalog + routing (`valeria/agenda`→`mateo/agenda`) + features (`features/valeria`→`features/mateo`) en el MISMO ticket (T-5) — sino 404 silencioso.
- Design-system-first: reusar `--agent-mateo` (#FEE209, ya existe), átomos Ribbon/SubTabsBar. Cero primitiva/token nuevo.
- Actualizar `// cap:` headers al mover features (`valeria.agenda` → `mateo.agenda`).
- Spanish neutro LatAm en labels ("Operar", "Plataforma") — sin voseo.

## Patterns forbidden (NEVER)
- ❌ `core/luana-core-*` (cualquier edición — sería `/pm-luana` lift).
- ❌ `comunify/`, `nicolify/`, `lupulo/` (cualquier path — scope gate M13).
- ❌ `tools/luana-cockpit/` (TOOL-SCOPE separado · F3/F4-consumer · dispatch aparte).
- ❌ `vitalia/backend/src/modules/` (esta story no toca DDD de módulos).
- ❌ `vitalia/frontend/src/components/ui/` (Shadcn primitives).
- ❌ Caja por defecto en migración (debe halt).
- ❌ Editar auto-gen a mano: `_actions-index.json`, `_code-index.json`, `modules/{m}.md`, `BACKLOG.*`.
- ❌ Grep-walker paralelo para actions-index (reusar `_code-index.json`).
- ❌ `toHaveScreenshot()` página completa fuera del scope Ribbon.
- ❌ Voseo en microcopy user-facing.
- ❌ `git add .`/`-A`; commit pelado en el hub (índice compartido).

## Files in scope (vitalia-scope)
- `scripts/map_zones_migration.py` (NEW) · `scripts/generate_actions_index.py` (NEW) · `scripts/validate_system_map.py` (MODIFY) · `scripts/reconcile_capabilities.py` (verify).
- `scripts/tests/test_map_zones_migration.py` (NEW).
- `vitalia/docs/product/capabilities/**/*.yaml` (re-tag 48 + nuevo platform/product-map-zonas.yaml).
- `vitalia/docs/architecture/SYSTEM-MAP.yaml` (promover zones) + `ADR-vitalia-005/004/003` + `SHELL-DESIGN-CONTRACT.md`.
- `vitalia/.claude/rules/shell-mockup-per-component.md` + `shell-feature-architecture-mandatory.md` · `vitalia/CLAUDE.md` · `.claude/skills/vitalia-design-system/SKILL.md`.
- `vitalia/docs/product/stories/vitalia-fase2-*/` (rename 5 + map_box en checkpoints).
- `vitalia/frontend/src/lib/agent-catalog.ts` · `components/shared/shell-organism/Ribbon.tsx` · `app/[tenantId]/(shell-organism)/{valeria→mateo}/` · `features/{valeria→mateo}/`.
- `vitalia/frontend/e2e/regression/vitalia-paradigm-map-zones/*.spec.ts` (NEW) + actualizar specs Valeria/Operar.
- `vitalia/frontend/src/__tests__/architecture/agent-catalog-ribbon-taxonomy.test.ts` (NEW).

## Files NEVER touch
- `core/luana-core-*/**` · `comunify/**` · `nicolify/**` · `lupulo/**`
- `tools/luana-cockpit/**` (dispatch tool-scope separado)
- `vitalia/backend/src/modules/**` · `vitalia/frontend/src/components/ui/**`
- `docs/process/capability-protocol.md` (protocol-scope cross-brand — dispatch separado)
- `.claude/rules/paradigm-arquitectura.md` (rule raíz cross-brand)

## must_load_skills (por surface)

### builder-backend (T-1, T-2, T-3, T-4)
- `backend-expert`
- `.claude/rules/paradigm-arquitectura.md`
- `.claude/rules/anti-orphan-integration.md`
- `.claude/rules/anti-duplication.md` (NO-NEW-LAYER actions-index)
- `.claude/rules/brand-docs-schema.md` (R2 archive · R3 auto-gen)
- `docs/process/capability-protocol.md` §7 (schema cap + map_box)

### builder-frontend (T-5, T-6 FE)
- `frontend-expert`
- `vitalia-design-system` (★ SSoT shell — único canal, no hereda overlay)
- `playwright-expert` (e2e Ribbon + ruta mateo/agenda)
- `.claude/rules/frontend-fsd.md`
- `.claude/rules/frontend-visual-fidelity.md`
- `.claude/rules/spanish-text.md`
- `.claude/rules/paradigm-arquitectura.md`

## Mockup gate
ADR-vitalia-003 **WAIVED** (`checkpoint.md::mockup_gate_waived: true`, Chris 2026-05-30). Sin mockups. Verificación visual = e2e Ribbon scoped.
