# T-4-result — F0 Rename backlog Fase 2 + map_box en checkpoints

**Story:** vitalia-paradigm-map-zones  
**Ticket:** T-4  
**Surface:** BE (docs)  
**Date:** 2026-05-30  

## Skills Consulted

| Skill | Por qué invocada | Decision tomada |
|---|---|---|
| `backend-expert` | Ticket classification docs/YAML manipulation, no production code | Confirm: pure docs ticket, native validators only (reconcile_capabilities.py) |
| `.claude/rules/brand-docs-schema.md` | Schema R1/R2 compliance for story dirs under `{brand}/docs/product/stories/` | Story dirs must carry `checkpoint.md`; git mv must preserve whole dir with chris-input.md per R4. Both satisfied. |
| `.claude/rules/paradigm-arquitectura.md` | map_zone derivation via SYSTEM-MAP.yaml zones registry (árbol de decisión) | map_zone derived from SYSTEM-MAP zones[] → never written per-cap by hand. map_box = the specific box within that zone. |
| `docs/process/capability-protocol.md` | cap_target field migration (config.* → configuracion.* / onboarding.* / valeria.* → mateo.*) | cap_target must match box.functional_area path from SYSTEM-MAP. Old config.*/valeria.* taxonomies retired per T-2. |

## Deliverables completed

### 1. git mv renames (5 story directories)

| Original | Nuevo |
|---|---|
| `vitalia-fase2-config-cuenta` | `vitalia-fase2-configuracion-cuenta` |
| `vitalia-fase2-config-conexiones` | `vitalia-fase2-configuracion-conexiones` |
| `vitalia-fase2-config-avanzado` | `vitalia-fase2-configuracion-avanzado` |
| `vitalia-fase2-config-onboarding-clinica` | `vitalia-fase2-onboarding-clinica` |
| `vitalia-fase2-valeria-pacientes` | `vitalia-fase2-mateo-pacientes` |

Each rename carries the full directory (checkpoint.md + chris-input.md + 01-spec.md where present).

### 2. checkpoint.md updates — ALL 22 vitalia-fase2-* stories

Added/updated fields in every checkpoint:
- `map_zone:` — derived from SYSTEM-MAP zones registry
- `map_box:` — specific box within zone
- `story_id:` — updated to new slug for renamed stories
- `agent_owner:` — updated to new taxonomy (config → configuracion/onboarding; valeria → mateo)
- `cap_target:` — updated old taxonomy refs (config.* → configuracion.*/onboarding.*; valeria.pacientes already correct)
- `last_modified:` — updated to 2026-05-30

### map_zone / map_box table applied

| Story pattern | map_zone | map_box | Notes |
|---|---|---|---|
| `configuracion-cuenta` | plataforma | configuracion | usuario ajusta, no agente |
| `configuracion-conexiones` | plataforma | configuracion | usuario ajusta, no agente |
| `configuracion-avanzado` | plataforma | configuracion | usuario ajusta, no agente |
| `onboarding-clinica` | plataforma | onboarding | alta + activación |
| `mateo-pacientes` | agentes | mateo | Mateo Operar/Mi Día — vista pacientes del día |
| `lisa-*` | agentes | lisa | agente opera Mi Clínica |
| `adrian-*` | agentes | adrian | agente opera Vender |
| `lucas-*` | agentes | lucas | agente opera Marketing |
| `camila-*` | agentes | camila | agente opera Reputación |

### 3. Release references updated

- `F2.yaml`: `vitalia-fase2-valeria-pacientes` → `vitalia-fase2-mateo-pacientes`; description text updated
- `F4.yaml`: 4 config-* stories → configuracion-*/onboarding-clinica new slugs

## Acceptance validators — GREEN

```
Validator 1: grep -L 'map_box:' vitalia/docs/product/stories/vitalia-fase2-*/checkpoint.md
→ 0 results (ALL have map_box)

Validator 2: ls vitalia/docs/product/stories/ | grep 'fase2-config-'
→ 0 results (zero dirs vitalia-fase2-config-* remaining)

Validator 3: grep 'cap_target: config\.\|cap_target: valeria\.' vitalia-fase2-*/checkpoint.md
→ 0 results (all old taxonomy cleaned)

Validator 4: scripts/reconcile_capabilities.py --brand vitalia
→ exit 0 (OK — all capabilities consistent with stories)
```

## Files changed

- 5 directories renamed via git mv (carries chris-input.md + checkpoint.md + 01-spec.md where present)
- 22 checkpoint.md files updated (map_zone + map_box + story_id + agent_owner + cap_target)
- `vitalia/docs/product/releases/F2.yaml` — story ref updated
- `vitalia/docs/product/releases/F4.yaml` — 4 story refs updated
- `vitalia/docs/product/stories/vitalia-paradigm-map-zones/T-4-result.md` — this file

Total: 5 renames + 22 checkpoint edits + 2 release edits = 29 file operations.
