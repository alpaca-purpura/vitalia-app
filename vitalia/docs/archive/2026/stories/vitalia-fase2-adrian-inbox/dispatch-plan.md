---
story_id: vitalia-fase2-adrian-inbox
brand: vitalia
autonomous_mode: true        # ★ Chris ratified 2026-06-03 ("cubre todos los pasos hasta done")
architecture_pattern: ADR-vitalia-004
---

# dispatch-plan — vitalia-fase2-adrian-inbox

> Autonomous build plan para `/dev-team`. **autonomous_mode: true** (Chris opt-in 2026-06-03).
> **HUMAN GATE (no autónomo):** `reviewing → done` requiere **Chris demo sign-off en dev-app** (Rule #37 + ADR-vitalia-008). El resto del ciclo (developing → developed → reviewing) corre autónomo: builder → auditor → fix-loop.

## Naturaleza

MIGRACIÓN + consolidación + un-stub. NO build virgen. El BE inbox + modelo + lista YA están shipped; el FE inbox rico vive huérfano. Riesgo bajo, scope acotado, sin superficie agéntica de producción → **safe para autonomous** salvo el gate humano del demo.

## Handoff matrix (ticket → agent → model → cost)

| Ticket | Surface | Agent | Model | Est. cost | Skills | Rationale del modelo |
|---|---|---|---|---|---|
| T-1 | BE | builder-backend | **sonnet** | ~M | backend-expert, sales-agent-expert(§anti-dup) | BE no-agentic; consume engine compliance. NO agentic production code → Sonnet (R23). |
| T-2 | BE | builder-backend | **sonnet** | ~M | backend-expert, sales-agent-expert | nudge consume tool vía resolver (no import). Sonnet OK. |
| T-3 | FE | builder-frontend | **sonnet** | ~S | frontend-expert, vitalia-design-system | ruta + registro CONN + ChannelBadge. Mirror pattern. |
| T-4 | FE | builder-frontend | **sonnet** | ~L | frontend-expert, vitalia-design-system | consolidación ~40 comps + DELETE huérfano. Mecánico-pesado pero guiado por § 9. |
| T-5 | FE | builder-frontend | **sonnet** | ~M | frontend-expert, vitalia-design-system | piezas NEW (3-pane, ModeToggle, ConversationModeButton). |
| T-6 | tests | builder-frontend | **sonnet** | ~M | frontend-expert, playwright-expert, vitalia-design-system | e2e + visual + a11y + demo-script. production_code=false. |

> **Ningún ticket es AGENTIC production code** → todos Sonnet (R23 cumplido: Opus obligatorio SOLO para agentic production; acá el agentic es consume-only). Auditores siempre Opus.

## DAG / lanes

```
        ┌── BE lane ──────────────┐
        │  T-1 ──→ T-2            │
START ──┤                         ├──→ T-6 (tests + demo) ──→ HUMAN GATE (Chris demo)
        │  T-3 ──→ T-4 ──→ T-5   │
        └── FE lane ──────────────┘
```

- **BE lane (T-1→T-2):** serializan (comparten `router.py`).
- **FE lane (T-3→T-4→T-5):** serializan (comparten `features/adrian/`).
- **BE y FE corren en paralelo** (sin deps cruzadas hasta T-6).
- **T-6** join: depende de T-1,T-2,T-4,T-5.
- **Bucket locks (M14):** `code:inbox` (BE) y `code:adrian` (FE) son módulos distintos → paralelos OK. Dentro de cada lane, serializar.

## Auditor routing

| Surface | Auditor | Model |
|---|---|---|
| BE (T-1, T-2) | auditor-backend | Opus |
| FE (T-3, T-4, T-5, T-6) | auditor-frontend | Opus |

Self-fix policy v4.2: mecánico (lint/format/typo/import) → Carril A (gate-verified). Comportamiento (mapping 3-modos, compliance gate, OCC) → Carril B (spawn dev-team TDD). Stake-asimétrico (PHI/tenant/audit/compliance) → Carril C (escalate Chris).

## Playwright visual scope

- `story_scope_routes`: `/{tenantId}/adrian/inbox`, `/{tenantId}/adrian/inbox?conv=*`
- `story_scope_components`: `features/adrian/components/inbox/**`, `components/shared/shell-organism/ChannelBadge.tsx`
- **forbidden (REUSE not modify):** `components/ui/**`, wrapper shell (`ShellOrganismLayout/ValeriaSidebar/Ribbon/SubTabsBar/EmptyState/SubSubTabsBar`)
- **out of scope:** `[conv-id]/page.tsx` N3-dyn (diferido), filtro "Asignadas a mí" (diferido — sin columna)
- 12 goldens: 3 modos × 2 themes × 2 (split/full). Ratchet shrink-only.

## Gates (gate-runner Haiku, post-build)

- BE: `test-vitalia` (arch fitness + inbox suite) — `cd vitalia/backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/inbox/ tests/architecture/`
- FE: `tsc --noEmit` + `eslint --max-warnings 0` + `vitest run src/features/adrian/ src/__tests__/architecture/`
- E2E: `E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/shell-organism/adrian-inbox` (base.ts anti-burbuja)
- `make ci-parity` pre-merge (sentinel `.ci-parity-deferred` → advisory dev-only; bidirectional cross_check_3 HARD)

## Anti-duplication / engine boundary guardrails (autonomous safety)

- ❌ Cero edición `core/` o `sales_agent/`/`copilot/` runtime — `av-no-core-edit` + `av-no-sales-agent-import` gates lo enforce.
- ❌ `features/inbox/` debe quedar BORRADO (`av-no-orphan-inbox`).
- Si cualquier builder detecta necesidad de tocar engine/sales_agent → STOP + escalate (NO ticketear).

## HUMAN GATE (★ no autónomo)

`reviewing → done` NO se cierra autónomo. Requiere:
1. `dod_live_verified: true` + `dod_evidence` (writes ejercidos en dev-app: PATCH mode→audit row, nudge→outbound row, modo conversación→Valeria colapsa, SC-3 PHI block; Console 0 errores, backend logs sin traceback).
2. `demo-script.md` ejecutado por Chris → `demo_signoff.result ∈ {APPROVED, APPROVED_WITH_NOTES(severity≤medium)}`.
3. `/pm-vitalia` Fase F: REFUSE merge sin lo anterior + poblar cap `adrian.inbox.yaml` (v3.2 blocks) + `git mv` story → archive.

## Resumen ejecutable

```
/dev-team vitalia vitalia-fase2-adrian-inbox autonomous
  → BE lane: T-1 (un-stub compliance) → T-2 (nudge)        [builder-backend sonnet]
  → FE lane: T-3 (ruta+registro) → T-4 (consolidación) → T-5 (piezas NEW)  [builder-frontend sonnet]
  → T-6 (e2e + visual + demo-script)                       [builder-frontend sonnet]
  → AUTO-HANDOFF /auditor (backend + frontend, Opus)
  → APPROVED → checkpoint reviewing
  → HUMAN GATE: Chris demo sign-off dev-app
  → /pm-vitalia merge → done + cap YAML + archive
```
