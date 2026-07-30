# Merge artifact — vitalia/vitalia-ux-discovery (parent SSoT cumplido)

> Brand: vitalia
> Closed: 2026-05-20 (Chris ratificó cierre como parent SSoT cumplido)
> Commit (squash-merge): n/a — story acts as parent SSoT, 17/56 tickets shipped via sibling sub-stories already merged (`vitalia-slice-1-infra-cross-cutting` + `vitalia-slice-1-onboarding-wizard` + `vitalia-copilot-tools-impl`)
> Worktree branch: wip/vitalia
> Auditor verdict: APPROVED (parent SSoT closure, no fresh code)
> Special closure: this story does NOT correspond to a single squash-merge commit. It produced the **ready package** that 7 sub-stories inherit. 3 sub-stories shipped already (audit verified). 5 sub-stories (Slice 1 UI) refined awaiting build per ola plan ratified 2026-05-20.

## § 1 — Gherkin verification matrix (parent SSoT inheritance)

> Esta story NO tiene gherkin scenarios propios — el parent 01-spec.md (412KB) define la totalidad del Slice 1. Los 17 tickets shipped (T-arch-1, T-infra-1..9, T-onboarding-1..7) cubren los scenarios de sus sub-stories. Los 40 tickets restantes (T-inbox/pipeline/agenda/fidelización/marketing) quedan heredados por las 5 sub-stories refined.

| Sub-story heredera | Tickets inheritados | Estado | Verificación |
|---|---|---|---|
| vitalia-slice-1-infra-cross-cutting | T-arch-1 + T-infra-1..9 (10) | ✅ done (squash 50143d57 + cc4fcd68) | 226/226 BE arch + 18/18 FE arch + downstream tests PASS |
| vitalia-slice-1-onboarding-wizard | T-onboarding-1..7 (7) | ✅ done (commit 4191371 + 38ab9bd) | Playwright E2E PASS_5_OF_5 |
| vitalia-copilot-tools-impl | T-agentic-1..3 absorbidos + tickets propios (12) | ✅ done (commits 3331151..427b0f3) | 1363/1363 tests + 16/16 goldens GREEN |
| vitalia-slice-1-inbox | T-inbox-1..9 (9) — heredados como referencia, sub-story produce 06-tickets propio post refresh | ⏸ refined (ola 1) | pending build per plan 2026-05-20 |
| vitalia-slice-1-pipeline | T-pipeline-1..7 (7) | ⏸ refined (ola 2) | pending build |
| vitalia-slice-1-agenda | T-agenda-1..9 (9) | ⏸ refined (ola 3) | pending build |
| vitalia-slice-1-fidelización | T-fidelización-1..7 (7) | ⏸ refined (ola 1) | pending build |
| vitalia-slice-1-marketing | T-marketing-1..8 (8) | ⏸ refined (ola 2) | pending build |

## § 2 — Playwright E2E run

> No E2E run propio (parent SSoT, no aplica). Verificación E2E ocurrió en sub-stories shipped:
> - `vitalia-slice-1-onboarding-wizard`: PASS_5_OF_5 (commits 4191371 + 38ab9bd)
> - `vitalia-auth-base-functional`: PASS (commit 9e7351f)

## § 3 — Capabilities updated/created (parent SSoT — no fresh caps)

> Esta story NO crea capabilities propias. Las 16 caps del Slice 1 ya fueron creadas por las 3 sub-stories shipped:
>
> - `compliance/hipaa-lite-defensive-stack` (infra-cross-cutting)
> - `iam/iam-scaffold-slice-1` (infra-cross-cutting)
> - `crm/crm-scaffold-slice-1` (infra-cross-cutting)
> - `observability/otel-sentry-graceful-degradation` (infra-cross-cutting)
> - `workers/idempotent-cron-arq-scaffold` (infra-cross-cutting)
> - `connections/registries-medical-vertical` (infra-cross-cutting)
> - `platform/design-tokens-foundation` (infra-cross-cutting)
> - `platform/migrations-slice-1-schema` (infra-cross-cutting)
> - `onboarding/clinic-onboarding-3step` (onboarding-wizard)
> - `onboarding/wizard_brand_studio_slice_1` (onboarding-wizard)
> - `copilot/valeria-wizard-onboarding-agentic` (copilot-tools-impl)
> - `agentic/medical-agentic-tools` (copilot-tools-impl)
> - `agentic/medical-safety-guardrails` (copilot-tools-impl)
> - `agentic/lucas-daily-analysis` (copilot-tools-impl)
> - `agentic/eval-goldens-slice-1` (copilot-tools-impl)
> - `sales_agent/adrian-3-tools-mvp` (copilot-tools-impl)
> - `sales_agent/state-overlay-langgraph` (copilot-tools-impl)
> - `sales_agent/medical-guardrails` (copilot-tools-impl)

Las 5 sub-stories Slice 1 UI restantes generarán sus propias capabilities al cerrar (estimadas 8-12 caps adicionales: inbox + pipeline + agenda + fidelización + marketing per módulo).

## § 4 — Modules MD refreshed (n/a)

> Esta story no agrega módulos propios — los 13 módulos vitalia ya fueron refrescados por sub-stories shipped.

## § 5 — How to verify (parent SSoT inheritance)

> Para verificar que el parent SSoT está cumplido reproducir estos comandos:

```bash
WS=$(git rev-parse --show-toplevel)

# 1. Verificar mockups heredados redistribuidos
ls ${WS}/vitalia/docs/product/stories/vitalia-slice-1-*/02-design-ui-mockup.html
ls ${WS}/vitalia/docs/archive/2026/stories/vitalia-slice-1-onboarding-wizard/02-design-ui-mockup.html

# 2. Verificar design tokens cementados en globals.css
grep -E "vitalia-(cian|purpura|amarillo|azul-marino|verde-lima)" ${WS}/vitalia/frontend/src/app/globals.css

# 3. Verificar 3 sub-stories heredereas shipped
ls ${WS}/vitalia/docs/archive/2026/stories/vitalia-slice-1-infra-cross-cutting/
ls ${WS}/vitalia/docs/archive/2026/stories/vitalia-slice-1-onboarding-wizard/
ls ${WS}/vitalia/docs/archive/2026/stories/vitalia-copilot-tools-impl/

# 4. Verificar 5 sub-stories heredereas refined
for s in inbox pipeline agenda fidelizacion marketing; do
  test -f ${WS}/vitalia/docs/product/stories/vitalia-slice-1-$s/checkpoint.md && echo "$s ✓"
done

# 5. Audit report 2026-05-20 disponible para retomar
test -f ${WS}/vitalia/docs/archive/2026/stories/vitalia-ux-discovery/audit-2026-05-20/AUDIT-REPORT.md && echo "audit report ✓"
```

**Expected:** todos los comandos retornan exit code 0 + archivos listados.

## § 6 — Inheritance carryover

Las 5 sub-stories Slice 1 UI heredan de este parent:

- **Mockups HTML SSoT visual** — distribuidos a cada `02-design-ui-mockup.html` (mismo commit del archive)
- **Design system tokens** — vivos en `vitalia/frontend/src/app/globals.css` (5 colores cian/púrpura/amarillo/marino/lima cementados por T-arch-1)
- **ADR-vitalia-001-shared-vs-fork.md** — sigue como referencia en `vitalia/docs/architecture/`
- **design-system.md** — sigue como referencia en `vitalia/docs/architecture/`
- **AUDIT-REPORT.md (2026-05-20)** — viajará al archive como referencia del replan
- **03-arch-{be,fe,agentic}.md (parent mega)** — viajará al archive como referencia (cada sub-story produce su propio 03-arch acotado tras refresh `/architect`)
- **04-validators.yaml (parent mega)** — viajará al archive; cada sub-story produce el suyo
- **05-guidelines.md (parent mega)** — viajará al archive; cada sub-story produce el suyo enfocado a reuso explícito (`nicolify/frontend/src/features/{...}` + `core/luana-core-*`)
- **06-tickets.yaml (parent mega)** — viajará al archive; cada sub-story produce 06-tickets propio post `/architect` refresh

Ratificación Chris (sesión 2026-05-20):

- ux-discovery → done (parent SSoT cumplido)
- Mockups deben moverse a sub-stories ANTES del archive (✓ hecho en este commit)
- Plan olas 2+2+1 (inbox+fidelización · pipeline+marketing · agenda)
- Side stories payment-adapter-mvp + fiscal-emission-pe arrancan refining EN PARALELO con Ola 1
- Proposal combinado `core-platform-extensions-slice-1` (cron_envelope + CompoundScopeRepositoryBase) ANTES de Slice 1
- Pre-flight gate Clerk+Playwright como hard gate
- Auto-handoff entre fases sin pedir confirmación intermedia
