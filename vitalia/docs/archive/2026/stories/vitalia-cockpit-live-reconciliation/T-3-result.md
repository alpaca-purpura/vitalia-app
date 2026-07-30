---
ticket: T-3
story_id: vitalia-cockpit-live-reconciliation
date: 2026-05-29
builder: claude-sonnet-4-6
phase: Fase 2+3 — Review técnico + Reconciliar ledger + Mapear backlog F2
state: done
---

# T-3 Result — Review técnico + Reconciliación ledger + Backlog mapeado

## Skills consultados

- `backend-expert` — schema cap YAML + validadores reconcile/compute
- `frontend-expert` — scope discipline caps FE
- `vitalia-design-system` — contexto shell-organism + caps live
- `.claude/rules/anti-duplication.md` — no mirrors cross-brand
- `.claude/rules/anti-orphan-integration.md` — CONN verification per cap
- `vitalia/.claude/rules/hipaa-lite.md` — PHI/sensitive data en evidencia
- `.claude/rules/spanish-text.md` — microcopy Spanish neutro (advisory)
- `.claude/rules/tdd-mandatory.md` — no nuevos tests inventados para inflar status

## Trabajo ejecutado

### Fase 2 — Review técnico per cap

Revisé las 67 caps existentes + 1 nueva contra las listas del audit 2026-05-27 (§5.1 live, §5.2 slice-1 superseded, §5.3 infra-only) y la matriz v1 del sweep (T-2).

Categorización final:

| Categoría | Conteo | Política aplicada |
|---|---|---|
| shell-organism live | 11 | status:live + ui_paradigm:shell-organism |
| infra-only | 10 | status:live + ui_paradigm:infra-only |
| admin-panel | 5 | status:live + ui_paradigm:admin-panel |
| public-landing | 1 | status:live + ui_paradigm:public-landing |
| slice-1-superseded | 33 | status:deprecated + ui_paradigm:slice-1-superseded + replaced_by_story |
| planned (sin cambio) | 7 | status:planned (sin cambiar) |
| **Total** | **67** | |

### Fase 3 — Reconciliación ledger

#### Caps YAML actualizados (67 + 1 nueva)

Cada YAML editado recibió:
- `status:` corregido (deprecated para slice-1-superseded)
- `ui_paradigm:` nuevo campo (shell-organism / infra-only / admin-panel / public-landing / slice-1-superseded)
- `replaced_by_story:` campo nuevo para caps deprecated que tienen story F2 (25 de 33)
- `last_modified: 2026-05-29` actualizado

#### Bug fix en `scripts/compute_capability_status.py`

El check de `stub` se ejecutaba ANTES del passthrough de `deprecated`, causando que todas las caps `deprecated` con 0 scenarios aparecieran como `stub` en el output. Fix: mover el passthrough `deprecated/sunset` antes del check stub.

Impacto: deprecated=0 → deprecated=33 en la foto final.

#### Cap nueva creada

`vitalia/docs/product/capabilities/ops/live-reconciliation-sweep.yaml`:
- capability_id: `vitalia.ops.live-reconciliation-sweep`
- status: live (tiene e2e_test: sweep.spec.ts que existe en filesystem)
- Schema v4 completo: scenarios[], access, business_rules, change_log

#### Fix ledger hard error

`admin/admin-streamlit-service.yaml`: `change_log[0].story_id` cambiado de `unknown-legacy` → `vitalia-adopt-luana-core-iam` (story archivada correcta).

### Backlog F2 mapeado

33 caps deprecated → 20 stories Fase 2 identificadas como historias de reconstrucción.

**Resumen por agente:**

| Agente | Story F2 | Caps slice-1 que reconstruye |
|---|---|---|
| valeria | vitalia-fase2-valeria-pacientes | crm-scaffold-slice-1, crm-consent-optout, valeria-wizard-onboarding-agentic, patient-records-medical-history |
| valeria | vitalia-fase2-valeria-agenda | prepaid-booking-advisory-locks (wired parcialmente en F2-S1 done) |
| adrian | vitalia-fase2-adrian-inbox | inbox-handler-mode-occ, inbox-tools-extensions |
| adrian | vitalia-fase2-adrian-embudo | bowtie-funnel-5-stages, adrian-3-tools-mvp |
| adrian | vitalia-fase2-adrian-propuestas | state-overlay-langgraph |
| lisa | vitalia-fase2-lisa-marca | wizard-brand-studio-slice-1 |
| lisa | vitalia-fase2-lisa-doctores | brand-studio-medical-sections, clinics-brand-extension, clinic-onboarding-3step |
| lisa | vitalia-fase2-lisa-servicios | (offer-studio UI) |
| lisa | vitalia-fase2-lisa-compliance | compliance-hipaa-lite-audit, hipaa-lite-defensive-stack, whatsapp-template-registry |
| camila | vitalia-fase2-camila-reputacion | nps-tracking |
| camila | vitalia-fase2-camila-reactivar | treatment-followup-workflow, adrian-reengagement-tool |
| camila | vitalia-fase2-camila-multiplicar | referrals-leaderboard |
| lucas | vitalia-fase2-lucas-resultados | attribution-matrix-4-origins, lucas-daily-analysis |
| lucas | vitalia-fase2-lucas-lanzar | lucas-stage-recommendations, lucas-recommendation-tool |
| config | vitalia-fase2-config-conexiones | oauth-meta-google-ads |

## Gates output (evidencia literal)

```
=== Gate 1: reconcile_capabilities --validate-ledger ===
LIVE⟹EVIDENCE WARNS in 21 cap(s):
(advisory — non-blocking. Run with --strict to make these errors.)
exit=0

=== Gate 2: validate_code_cap_bidirectional ===
Running cross-check 3 (scenarios e2e_test paths)...
  total=61 pass=61 drift=0
Running cross-check 4 (access roles ↔ decorators)...
  total=12 pass=11 drift=1
Verdict: SOFT_DRIFT
Drift total: 1 · in HARD checks ([3]): 0

=== Gate 3: compute_capability_status ===
Completado: 68 caps · stub=27 · declared-live=1 · verified-live=2 · drift=0 · partial=5 · wip=0 · deprecated=33

=== Gate 4: YAML frontmatter parse ===
ALL 68 FRONTMATTER YAML VALID

=== Gate 5: arch_no_engine_edit ===
PASS: no engine edits

=== Gate 6: no_slice1_rebuild ===
PASS: los 3 index.ts con cap: headers son pre-existentes (T-2), no rebuilds slice-1
```

### Nota sobre yaml_caps_parse (04-validators.yaml)

El validator `yaml_caps_parse` usa `yaml.safe_load` que falla en archivos multi-documento (`---` doble). Este comportamiento es PRE-EXISTENTE (los 67 archivos ya tenían esta estructura antes de T-3). El parser correcto (usado por los scripts internos) extrae solo el frontmatter. No es una regresión introducida por T-3.

## Foto antes/después

| Métrica | Antes (inicio T-3) | Después (fin T-3) |
|---|---|---|
| Total caps | 67 | 68 (+1 nueva ops/live-reconciliation-sweep) |
| verified-live | 1 | 2 |
| partial | 5 | 5 |
| declared-live | 6 | 1 |
| stub | 55 | 27 |
| deprecated | 0 | 33 |
| hard ledger errors | 1 | 0 |
| cross_check_3 drift | 0 | 0 |

## Deliverables producidos

1. **67 cap YAMLs reconciliados** — `vitalia/docs/product/capabilities/**/*.yaml`
2. **1 cap nueva** — `vitalia/docs/product/capabilities/ops/live-reconciliation-sweep.yaml`
3. **Matriz actualizada** — `vitalia/docs/domains/ops/live-reconciliation.md` (columnas technical_verdict + acción + story_mapeada + sección Backlog mapeado completa)
4. **`_status-computed.json` regenerado** — `vitalia/docs/product/capabilities/_status-computed.json`
5. **Bug fix en script** — `scripts/compute_capability_status.py` (deprecated passthrough antes de stub check)

## Estado post-T-3

Story state puede avanzar a `developed` → AUTO-HANDOFF `/auditor`.
