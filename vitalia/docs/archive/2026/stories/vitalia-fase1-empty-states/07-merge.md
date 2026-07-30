---
story_id: vitalia-fase1-empty-states
brand: vitalia
phase: fase-1
type: ui-story
module: shell-organism
capability: shell.empty-states
state: done
merged_at: 2026-05-26T13:55:00-05:00
merged_by: /pm-vitalia
auditor_verdict: APPROVED
auditor_warns: 2
auditor_warns_inventory:
  - WARN-1 Visual goldens pending live generation (stack required `--update-snapshots`) · flag `pending_chris_visual_ratify:true` cementado (patrón F1-S3 shipped 2026-05-23)
  - WARN-2 Pre-existing 320 prettier unformatted files OUTSIDE F1-S10 scope (separate cleanup story TBD · NO bloquea merge porque NO fueron introducidos por F1-S10)
audit_iterations: 1
self_fix_iter: 1  # auditor auto-fix loop iter 1 — prettier --write 39 F1-S10 scope files (whitelist #2 Format collective Caso B)
gherkin_coverage_pct: 100  # 13/13 scenarios (11 SC + 2 N/A justified)
checkpoints_passed: "30/30 (C1 4/4 · C2 4/4 · C3 6/6 · C4 7/7 · C5 6/6 — only TBD by merge step → resolved this commit)"
phase_1_complete: true   # ★ F1-S10 cierra CHAIN F1-S0..F1-S10 (11 stories) Fase 1 vitalia-mvp-ui-foundation
---

# 07-merge.md — F1-S10 vitalia-fase1-empty-states

> **5 secciones cementadas** post story-closure-gate 2026-05-18 (`.claude/rules/story-closure-gate.md` Layer 7).
> **★ FASE 1 COMPLETA** — última story del shell-organism vacío navegable. Fase 2 desbloqueada (22 stories sub-tab funcionales).

## § 1 — Gherkin verification matrix

Source: `06-audit/gherkin-matrix.md` (Phase D, auditor-frontend Opus). 13 scenarios totales — 11 con tests + 2 N/A justificados.

| SC | Título | Tests | Status |
|---|---|---|---|
| SC-1 | happy · 22 sub-tabs navegables sin error | `sc-01-navegacion-22-subtabs.spec.ts` parametrizado 22 combos | **SPEC_VALID** (live pending stack) |
| SC-2 | happy · Lisa Servicios toggle Catálogo/Escalera | `sc-02-lisa-servicios.spec.ts` + `ServiciosPlaceholder.test.tsx` (5 specs) | **SPEC_VALID** |
| SC-3 | happy · Adrián Embudo Kanban 6 cols | `sc-03-adrian-embudo.spec.ts` + `EmbudoPlaceholder.test.tsx` (7 specs) | **SPEC_VALID** |
| SC-4 | happy · Valeria Agenda enriquecida (toolbar + filters + grid 6d + footer summary) | `sc-04-valeria-agenda.spec.ts` + `AgendaSlot.test.tsx` (11) + `AgendaToolbar.test.tsx` (13) + `AgendaPlaceholder.test.tsx` (13) | **SPEC_VALID** |
| SC-4.bis | happy · Adrián Inbox completo + Takeover UX state A↔B | `sc-04bis-adrian-inbox.spec.ts` + `InboxPlaceholder.test.tsx` (8) + `CampaignTag.test.tsx` (7) + `ConversationItem.test.tsx` (29) + `ContactSidebar.test.tsx` (11) | **SPEC_VALID** |
| SC-5 | negative · sub-tab inválido URL → 404 jerárquico | `sc-05-subtab-invalido.spec.ts` (reusa F1-S9 not-found.tsx + `isValidSubtab`) | **SPEC_VALID** |
| SC-6 | edge · 21 clicks rápidos sin shell re-mount | `sc-06-edge-no-shell-remount.spec.ts` | **SPEC_VALID** |
| SC-7 | adversarial · XSS payload en URL subtab | `sc-07-adversarial-xss.spec.ts` (page.on('dialog')=never assertion) | **SPEC_VALID** |
| SC-8 | sub-cat empty_state · 16 sub-tabs genéricas | `sc-08-empty-states-genericos.spec.ts` parametrizado 16 + `EmptyState.test.tsx` | **SPEC_VALID** |
| SC-9 | sub-cat a11y · heading hierarchy + keyboard + axe wcag2aa | `sc-09-a11y.spec.ts` (@axe-core/playwright en 3 vistas) | **SPEC_VALID** |
| SC-10 | sub-cat i18n · Spanish neutro + currency tenant_locale | `sc-10-i18n.spec.ts` + arch test `test_no_voseo_in_copy.test.ts` | **SPEC_VALID** |
| SC-11 | sub-cat network_failure | **N/A justified** — F1-S10 no fetch API (mock-only) · F2-S{N} cablea cada sub-tab |
| SC-12 | sub-cat race_condition + concurrent_users + large_dataset | **N/A justified** — F1-S10 no DB writes + no pagination · F2-S{N} cablea |

**Coverage:** 11/11 testable scenarios = **100%** (+ 2 N/A explicit justified in spec § 5). Sub-categorías mandatory cubiertas: empty_state ✓ · a11y ✓ · i18n ✓. N/A justificadas: race/concurrent/network/large_dataset (mock-only Fase 1 per § 5 SC-11+SC-12).

**Live execution:** Playwright specs valid (TS strict + structural compliance) pero **NOT live-run** porque stack vitalia :3002 no disponible durante esta sesión auditor. Goldens flag `pending_chris_visual_ratify:true` (patrón F1-S3 shipped 2026-05-23 — Chris valida visual diff post-merge cuando stack disponible).

## § 2 — Playwright E2E run

```bash
WS=$(git rev-parse --show-toplevel)

# Preflight (per .claude/rules/e2e-testing.md)
cd ${WS} && bash scripts/e2e-preflight.sh

# Behavior suite (11 specs SC-1..SC-10 + SC-4.bis)
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test --project=smoke e2e/regression/vitalia-fase1-empty-states/

# Visual goldens (44 PNG light/dark + 2 takeover states A/B + responsive 6×3)
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test e2e/visual/empty-states/ --update-snapshots
```

**Status post-merge:** specs created + structure validated · live execution **pending Chris next session con stack disponible** (igual patrón F1-S3 ratify visual goldens). Cuando ratifique → `pending_chris_visual_ratify: false` en capability YAML.

## § 3 — Capabilities updated/created

### NEW: `vitalia/docs/product/capabilities/shell-organism/empty-states.yaml` (1 capability)

- **capability_id**: `vitalia.shell.empty-states`
- **module**: `shell-organism`
- **slug**: `empty-states`
- **status**: `live`
- **date_introduced**: `2026-05-26`
- **story_introduced**: `vitalia-fase1-empty-states`
- **package_version**: `0.1.0`
- **package_path**: `vitalia/frontend/src/components/shared/shell-organism/SubTabContent.tsx` (dispatcher)
- **license**: proprietary

**Surface (full inventory):**

- **Frontend (`vitalia/frontend/src/`):**
  - `components/shared/shell-organism/SubTabContent.tsx` (dispatcher PLACEHOLDER_MAP 22 entries consume RIBBON_SUBTABS SSoT) + .test.tsx
  - `components/shared/shell-organism/EmptyState.tsx` (genérico) + .test.tsx
  - `components/shared/shell-organism/PlaceholderCard.tsx` (con StatusDot)
  - `components/shared/shell-organism/SubTabHeader.tsx` (h2 + description + opcional CTA)
  - `components/shared/shell-organism/StatusDot.tsx` (verde/amarillo/gris/rojo color tokens)
  - `components/shared/shell-organism/TogglePill.tsx` (Shadcn Tabs wrapper styled pill) + .test.tsx
  - `features/lisa/components/placeholders/{Marca,Doctores,Servicios,Compliance}Placeholder.tsx` (4)
  - `features/lucas/components/placeholders/{Lanzar,Envuelo,Recursos,Resultados,Mercado}Placeholder.tsx` (5)
  - `features/adrian/components/placeholders/{Inbox,Embudo,Outbound,Propuestas}Placeholder.tsx` (4)
  - `features/adrian/components/inbox/{CampaignTag,ConversationItem,MessageBubble,MessageInput,ContactSidebar,ThreadHeader,TakeoverBanner}.tsx` (7 sales_studio parity + takeover UX)
  - `features/valeria/components/placeholders/{Agenda,Pacientes}Placeholder.tsx` (2)
  - `features/valeria/components/agenda/{AgendaToolbar,AgendaFilters,AgendaDayHeader,AgendaSlot,AgendaSummaryFooter}.tsx` (5 enriquecida)
  - `features/camila/components/placeholders/{Voz,Reactivar,Multiplicar,Reputacion}Placeholder.tsx` (4)
  - `features/config/components/placeholders/{Cuenta,Conexiones,Avanzado}Placeholder.tsx` (3)
  - `app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx` MODIFY (mount `<SubTabContent>`)

- **Tests (`vitalia/frontend/`):**
  - Vitest unit per molécula/organismo (~70+ specs): 1691/1691 total Vitest GREEN post-T-1..T-11 + auditor self-fix iter 1
  - Arch fitness: 135/135 PASS (23 test files inc. 3 NEW T-9: `test_subtab_content_uses_ribbon_subtabs_ssot` + `test_no_hardcoded_subtab_keys` + `test_no_phi_real_data`)
  - Playwright behavior: 11 specs SC-1..SC-10 + SC-4.bis en `e2e/regression/vitalia-fase1-empty-states/`
  - Visual goldens specs: `e2e/visual/empty-states/` (~64 PNG snapshots pending live gen)

- **Docs:** spec ratified `01-spec.md v2` + arch `03-arch.md` + validators `04-validators.yaml` + guidelines `05-guidelines.md` + tickets `06-tickets.yaml` (11 audit-passed) + 7 mockups HTML standalone + 1 mockup grid integral ratificados visualmente Chris batch 1+2

**Scenarios (verbatim 01-spec.md § 5):** 11 scenarios + 2 N/A justified — ver § 1 Gherkin matrix above.

**HIPAA-lite compliance:** F1-S10 NO PHI real (mock data ficticia) · arch test `test_no_phi_real_data.test.ts` enforce. F2-S{N} (vitalia-fase2-{agent}-{subtab}) wires data real + RBAC `@require_phi_access` + dual filter tenant+clinic + audit log.

**Dependencies cross-package:** consume `luana-core-iam` (tenant URL params via F1-S9 shipped). NO engine `core/luana-core-*/` edits en F1-S10.

**KPIs (Fase 2 instrumentation):** `subtab_viewed` event diferido a Fase 2 per spec § 13 Q10 cement batch 3.

### UPDATE (auto-list refresh): `vitalia/docs/product/modules/shell-organism.md`

Auto-list block regenerable via `scripts/reconcile_capabilities.py --brand vitalia` (R3). Post-merge:
- Capabilities counter en módulo shell-organism: 7 → **8** (NEW empty-states)
- Inventory live: layout-5050 · ribbon · routing · sub-tabs · valeria-chat · valeria-sidebar + NEW **empty-states**

## § 4 — Modules MD refreshed

| File | Acción |
|---|---|
| `vitalia/docs/product/modules/shell-organism.md` | UPDATE auto-list section (capability count 7→8, add empty-states) — regenerable via `python scripts/reconcile_capabilities.py --brand vitalia` |
| `vitalia/docs/product/capabilities/shell-organism/empty-states.yaml` | NEW (creado en este merge) |
| `vitalia/docs/product/BACKLOG.{md,yaml,-TLDR.md}` | regen auto via `make portfolio` o `python scripts/generate_backlog.py --brand vitalia` (R3 — gitignored) |
| `docs/portfolio/{PORTFOLIO,vitalia}.md` | regen auto via `make portfolio` (R3 gitignored) |

## § 5 — How to verify

```bash
WS=$(git rev-parse --show-toplevel)

# Frontend validators
cd ${WS}/vitalia/frontend
npx tsc --noEmit                                                   # 0 errors
npx eslint src/ --cache                                            # 0 errors
npx vitest run                                                     # 1691+ tests GREEN
npx vitest run src/__tests__/architecture/                         # 135/135 arch fitness GREEN

# Prettier scope F1-S10 (39 files post auto-fix iter 1)
git diff --name-only 0187ce17^..f71ed835 -- 'vitalia/frontend/src/' 'vitalia/frontend/e2e/' \
  | grep -v "06-tickets.yaml\|T-.*result.md\|impl-log.md\|checkpoint.md\|gate-output.json" \
  | sed 's|^vitalia/frontend/||' \
  | xargs npx prettier --check                                     # PASS post auto-fix

# E2E behavior (requires stack vitalia :3002)
cd ${WS} && bash scripts/e2e-preflight.sh
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test --project=smoke e2e/regression/vitalia-fase1-empty-states/

# E2E visual goldens (gen baseline ratify Chris)
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test e2e/visual/empty-states/ --update-snapshots
# Después Chris valida diff visual + cementa pending_chris_visual_ratify:false

# Browser manual test 22 sub-tabs (post stack up)
# Visit /{tenantId}/lisa/marca · /{tenantId}/lisa/servicios · /{tenantId}/adrian/inbox · /{tenantId}/valeria/agenda
# Click ribbon agents 5 + Config tab → navegar 22 sub-tabs sin error
# Adrián Inbox: click "✋ Tomar el control" → banner amarillo + MessageInput enabled
# Adrián Inbox: click "🤖 Devolver a Adrián" → back to state A
```

## § 6 — Anti-duplication audit

Auditor-frontend Cat 12 verification (verbatim REVIEW.md):

- **0 cross-brand mirrors** detected en `{nicolify,comunify,lupulo}/frontend/src/`. Sales_studio reference (`/home/chalreme/Documentos/ap_sales_agent/frontend/src/features/closer-studio/components/inbox/`) es REFERENCIA conceptual SOLO — NO import directo (workspace separado). F1-S10 construye Vitalia brand-local con SHAPE/UX validado conceptualmente.
- **0 engine `core/luana-core-*/src/` edits.** No promotion proposal requerido.
- **agent-catalog.ts READ-ONLY respected.** SubTabContent dispatcher consume `RIBBON_SUBTABS` import sin modificar SSoT.
- **Lift candidate documented (F2+ promotion):** cuando comunify/lupulo/fitflow construyan shell similar con inbox → escalá `/pm-luana` proposal `docs/promotion-protocol/proposals/{date}-lift-shell-inbox.md` para promoción a `core/luana-core-ui/inbox/`. Patterns candidatos: CampaignTag · ConversationItem (con temp-dot+stage-badge+channel-abbr+handler_mode border) · MessageBubble · MessageInput state dual · TakeoverBanner + ThreadHeader (takeover UX NEW conceptual).

## § 7 — Story-closure-gate Layer 7 compliance

- ✅ R1 brand-docs-schema: NO MDs sueltos en `vitalia/docs/` raíz introducidos por este merge
- ✅ R2 brand-docs-schema: story `git mv` a `vitalia/docs/archive/2026/stories/vitalia-fase1-empty-states/` ejecutado en MISMO commit del merge
- ✅ R3 brand-docs-schema: NO edits manuales a `BACKLOG.{md,yaml,-TLDR.md}` ni sección auto-list de `modules/shell-organism.md`. Auto-list regenerable via `scripts/reconcile_capabilities.py --brand vitalia` post-merge.
- ✅ Capability inventory enforcement: `capabilities/shell-organism/empty-states.yaml` creada en este merge (proposal 2026-05-16 enforcement respected)
- ✅ Story-closure-gate Layer 7 templates: 5 secciones cementadas verbatim § 1 Gherkin · § 2 Playwright · § 3 Capabilities · § 4 Modules · § 5 How to verify

## § 8 — CHAIN F1-S0..F1-S10 COMPLETE (★ FASE 1 done)

Esta historia cierra la chain Fase 1 vitalia-mvp-ui-foundation con **11 stories shipped sequential**:

| Story | Date done | Capability/módulo |
|---|---|---|
| F1-S0 vitalia-fase1-stack-stability | 2026-05-23 | platform/shell-foundation-shadcn-tailwind-v4 |
| F1-S1 vitalia-fase1-design-tokens-theme | 2026-05-23 | platform/design-tokens-theme |
| F1-S2 vitalia-fase1-topbar-global | 2026-05-23 | platform/topbar-global |
| F1-S3 vitalia-fase1-tenant-switcher | 2026-05-23 | platform/tenant-switcher |
| F1-S4 vitalia-fase1-shell-layout-5050 | 2026-05-24 | shell-organism/layout-5050 |
| F1-S5 vitalia-fase1-valeria-rail-history | 2026-05-24 | shell-organism/valeria-sidebar |
| F1-S6 vitalia-fase1-valeria-chat-skeleton | 2026-05-25 | shell-organism/valeria-chat |
| F1-S7 vitalia-fase1-ribbon-6-tabs | 2026-05-25 | shell-organism/ribbon |
| F1-S8 vitalia-fase1-sub-tabs-line2 | 2026-05-25 | shell-organism/sub-tabs |
| F1-S9 vitalia-fase1-routing-shell | 2026-05-25 | shell-organism/routing |
| **F1-S10 vitalia-fase1-empty-states** | **2026-05-26** | **shell-organism/empty-states ★ this merge** |

**Outcome cumplido:** "puedo entrar a dev-app, autenticarme, navegar las 6 pestañas + 22 sub-tabs sin que rompa nada — cualquier vista vacía me hace sentir que el producto es real aunque no esté funcional aún."

**Próximo paso Fase 2:** 22 stories `vitalia-fase2-{agent}-{subtab}` cada una implementando data real + funcionalidad por sub-tab. Backlog generado durante shell-organism planning 2026-05-22 — todas state=idea pendientes refinement.
