<!-- voseo-allowed: merge artifact may cite spec scenario gherkin verbatim per R25 -->
# 07-merge.md — vitalia-fase1-valeria-chat-skeleton (F1-S6)

> Brand: vitalia · PM: `/pm-vitalia` · Auditor verdict: APPROVED · Merge date: 2026-05-25
> Story closure gate (`.claude/rules/story-closure-gate.md`) — 5 secciones cementadas

---

## § 1 — Gherkin verification matrix

Snapshot del `06-audit/gherkin-matrix.md` (auditor Phase D) — 7/7 scenarios PASS:

| # | Scenario | Test path | Status |
|---|---|---|---|
| SC-1 | happy render mock messages | `e2e/shell-organism/valeria-chat-happy.spec.ts` + unit ValeriaChat/ChatMessages/ChatHeader | PASS |
| SC-2 | send mock message | `valeria-chat-send.spec.ts` + ChatComposer + chat-store unit | PASS |
| SC-3 | Shift+Enter / Enter / IME guard | `valeria-chat-keys.spec.ts` + ChatComposer keyDown matrix | PASS |
| SC-4 | adversarial XSS | `valeria-chat-xss.spec.ts` + MessageBubble text-escape | PASS |
| SC-5 | empty_state | `valeria-chat-empty.spec.ts` + ChatMessages EmptyState branch | PASS |
| SC-6 | accessibility wcag2aa | `valeria-chat-a11y.spec.ts` + axe-core | PASS |
| SC-7 | i18n Spanish neutro | `valeria-chat-i18n.spec.ts` + arch test no-voseo | PASS |

Cobertura: **100% (7/7)** scenarios mandatory v4.1 sub-categorías aplicables (empty_state + accessibility + i18n) + 4 base (happy/negative→edge/adversarial). Sub-categorías N/A justificadas en `04-validators.yaml::sub_categories_coverage` (race/concurrent/network/large — mock chrome sin DB/fetch real).

---

## § 2 — Playwright E2E run

| Suite | Command | Result | Source |
|---|---|---|---|
| Behavior (4 specs, 26 tests) | `cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke e2e/shell-organism/valeria-chat-*.spec.ts` | PASS 26/26 | T-8 builder live stack run |
| Visual goldens (4 PNG) | `npx playwright test e2e/shell-organism/valeria-chat-visual.spec.ts --update-snapshots` | PASS 4/4 | T-9 builder live stack run |
| A11y axe wcag2aa | `npx playwright test e2e/shell-organism/valeria-chat-a11y.spec.ts` | PASS | T-9 |
| i18n Spanish neutro | `npx playwright test e2e/shell-organism/valeria-chat-i18n.spec.ts` | PASS | T-9 |
| Vitest unit (full suite) | `cd vitalia/frontend && npx vitest run` | 1189/1189 PASS | T-9 + auditor independent re-run |
| Arch fitness (90 tests) | `cd vitalia/frontend && npx vitest run src/__tests__/architecture/` | 90/90 PASS | T-9 + auditor re-run |
| tsc strict | `cd vitalia/frontend && npx tsc --noEmit` | 0 errors | auditor re-run |
| ESLint 60+ rules | `cd vitalia/frontend && npx eslint src/ e2e/` | 0 errors | auditor re-run (post 1 self-fix) |

**Live re-verification deferida a post-merge** (auditor re-corrió unit/arch/lint/tsc independientemente; behavior + visual + a11y + i18n confiados a builder verdicts + gate-output.json — todos GREEN).

Visual goldens: 4 PNG en `vitalia/frontend/e2e/__screenshots__/visual/valeria-chat-visual.spec.ts/` (populated/empty × light/dark), 37-55 KB cada uno.

---

## § 3 — Capabilities updated/created

### Created

- **`vitalia/docs/product/capabilities/shell-organism/valeria-chat.yaml`** (NEW)
  - `capability_id: vitalia.shell-organism.valeria-chat`
  - `module: shell-organism`
  - `slug: valeria-chat`
  - `status: live` (planned → live, primera vez shipped)
  - `date_introduced: 2026-05-25`
  - `story_introduced: vitalia-fase1-valeria-chat-skeleton`
  - Surfaces: 7 NEW components + 1 catalog SSoT + 1 zustand store + 1 mock fixture + 8 tests + 1 NEW arch test + 7 NEW E2E + 4 PNG goldens
  - Dependencies cross-package: ninguna (brand-local; flagged LIFT CANDIDATE cross-brand)

### Updated

- `vitalia/docs/product/modules/shell-organism.md` — auto-list section regenerada por `scripts/reconcile_capabilities.py --brand vitalia` para incluir entry de `valeria-chat`
- `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md` — F1-S6 marcado como done; `recently_done` updated en brand checkpoint

---

## § 4 — Modules MD refreshed

Single module afectado:

- **`vitalia/docs/product/modules/shell-organism.md`** — sección auto-list (`<!-- AUTO-GENERATED -->` block) regenerada post-merge para incluir `shell.valeria-chat` capability YAML. Manual intro/decisiones cardinales sección PRESERVED (no editada manualmente per R3 — el block auto-list se regenera vía `scripts/reconcile_capabilities.py --brand vitalia`).

Decisión cardinal nueva (manual intro): `valeria-chat` adopta `agent-catalog.ts` SSoT cross-shell consumido también por `Ribbon` (F1-S7 futuro) + `ValeriaRail`. **LIFT CANDIDATE** flagged en file header — cross-brand cuando ≥2 brands implementen chat agéntico (hoy solo vitalia; Nicolify CopilotSidebar es concepto similar pero implementación brand-local independiente).

---

## § 5 — How to verify

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend

# 1. Type-check + lint (rápidos)
npx tsc --noEmit                                    # 0 errors esperado
npx eslint src/components/shared/shell-organism/ src/lib/agent-catalog.ts src/stores/chat-store.ts --max-warnings 0

# 2. Vitest unit + coverage
npx vitest run src/components/shared/shell-organism/ src/lib/__tests__/agent-catalog.test.ts src/stores/__tests__/chat-store.test.ts --reporter=verbose
# Esperado: 294+/294+ PASS (1189 full suite si corres todo)

# 3. Arch fitness (incluye NEW test-agent-catalog-ssot)
npx vitest run src/__tests__/architecture/test-agent-catalog-ssot.test.ts --reporter=verbose
# Esperado: 3/3 PASS

# 4. Stack up (si querés Playwright)
cd ${WS} && make dev-vitalia
# Wait ~30s

# 5. Playwright behavior + visual + a11y + i18n
cd ${WS}/vitalia/frontend
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke \
  e2e/shell-organism/valeria-chat-*.spec.ts \
  --reporter=list

# 6. Visual goldens (regenerar si dev cambia tokens)
E2E_BASE_URL=http://localhost:3002 npx playwright test \
  e2e/shell-organism/valeria-chat-visual.spec.ts \
  --reporter=list

# 7. Visual inspection en navegador (opcional)
# Abrir http://localhost:3002/<tenant-id>/lisa/marca
# Verificar:
#  - ChatHeader: avatar Valeria (real img + status dot verde + Mode Pill "🤖 Modo agente")
#  - 6 mensajes mock + delegate marker Camila + thinking dots Camila
#  - Composer: textarea + 3 stubs (📎/🎙️/⚡) + botón "Enviar" purple
#  - Empty state si reset: ilustración Valeria grande + heading "Empieza una conversación" + subtexto tuteo
#  - Dark mode toggle preserva chat
#  - Cmd+K enfoca composer
```

---

## Merge metadata

- **Branch:** `wip/vitalia` (canónico)
- **9 commits del story** (T-1..T-9 + docs):
  - `c2ba2b89` T-1 agent-catalog + globals.css tokens
  - `76eaa919` T-2 chat-store + mocks (+ T-3 component files absorbed via parallel race — non-destructive; commit hygiene only — see `gate-output.json::tickets_summary.race_condition_note`)
  - `ef879cd1` T-4 ChatComposer
  - `81061d28` T-5 ValeriaChat + ChatMessages + EmptyState
  - `4820bb2c` T-6 integration MODIFY ValeriaSidebar + DELETE ChatSlot
  - `0da5cc16` T-7 POM + fixtures
  - `b804eb73` T-8 4 Playwright behavior specs
  - `d4341ad7` T-9 visual goldens + a11y + i18n + empty state
- **Auditor self-fix:** F-1 unused eslint-disable directive removed (1 line, Caso C whitelist Cat #1)
- **Total LOC delta:** ~2150 prod + ~650 tests (per architect estimate, matches actual)
- **9/9 tickets audit-passed**, 1/3 audit_iterations cap (no fix-loop required)

## Decisions honored (D1-D9 from spec § 0)

All 9 cardinal decisions cementadas durante /po-ux iter v3 honored verbatim por architect + builders:

- D1 ChatHeader evoluciona F1-S5 (avatar + name preservados + Mode Pill agregado + status text largo)
- D2 Mock send determinístico `count % len` (4 canned responses Spanish neutro)
- D3 Composer 3 stubs visuales (📎/🎙️/⚡) con `title="próximamente"`, sin handlers
- D4 DelegateMarker italic centered + "(modo Mantener)"
- D5 TypingIndicator rico (name + acción + 3 dots)
- D6 Spanish neutro hardcoded en MOCK_MESSAGES (tuteo); F2-S11 wire voz tenant runtime
- D7 Timestamps debajo del bubble (text-[10px] muted)
- D8 Visual gate único file `valeria-chat-sample.html` 2 variantes (A 6-msgs + B empty)
- D9 ChatHeader+MessageBubble parametrizados por `agent: AgentSlug` (futuro selector switch zero re-trabajo)
