# Cockpit Permissions — Qué transitions hace Chris vs Claude (v1 cement 2026-05-27)

**Cement-date:** 2026-05-27.
**Origen:** plan `/home/chalreme/.claude/plans/ok-lo-apruebo-realiza-cheeky-harbor.md` § Phase 1.1.D.

> El cockpit es la interfaz visual al SDD. Chris hace transitions humanas (priorizar/despriorizar/parquear/dropear), Claude (via skills) hace transitions de proceso (refined/ready/developing/developed/reviewing/done). El cockpit enforce esta separación.

---

## CHRIS_ALLOWED_TRANSITIONS (whitelist verbatim)

El endpoint `POST /api/transition` del cockpit SOLO permite las siguientes transitions cuando se llama desde el UI (asume actor=Chris). Otras transitions → 403 con mensaje "esto lo hace skill {X}".

| Desde | Hacia | Acción Chris | Verbo cockpit |
|---|---|---|---|
| `idea` | `refining` | Priorizar para refinamiento | "Empezar a refinar" |
| `idea` | `parked` | Pausar (con razón) | "Parquear" |
| `idea` | `dropped` | Descartar terminal (con razón) | "Descartar" |
| `refining` | `idea` | Despriorizar / volver al backlog | "Volver a backlog" |
| `refining` | `parked` | Pausar (con razón) | "Parquear" |
| `refining` | `dropped` | Descartar terminal (con razón) | "Descartar" |
| `parked` | `idea` | Reactivar | "Reactivar" |

**Razón obligatoria en `parked` y `dropped`:** cockpit pide string ≥10 chars al hacer la transition. Se persiste en `checkpoint.md::parked_reason` o `checkpoint.md::dropped_reason`.

**`dropped` es terminal:** una story dropped NO puede pasar a otro state (a diferencia de parked). Si Chris cambia de idea sobre una dropped, debe crear una story nueva.

---

## STATE_OWNER (quién cambia cada state)

| State | Owner skill | Trigger |
|---|---|---|
| `idea` | Chris + `/pm-{sistema}` | story creada manual o desde idea del backlog |
| `refining` | Chris (cockpit) o `/pm-{sistema}` | priorizar para refinamiento |
| `refined` | `/architect` (cierra spec) o `/pm-{sistema}` (ratifica) | Chris ratifica spec + diseño |
| `ready` | `/architect` | ready package completo (4 archivos canónicos) |
| `developing` | `/dev-team` | builder spawn empieza |
| `developed` | `/dev-team` | validators GREEN |
| `reviewing` | `/auditor` (AUTO-HANDOFF desde developed) | audit start |
| `done` | `/pm-{sistema}` (Fase F MERGE) | auditor APPROVED + merge a main |
| `parked` | Chris (cockpit) | pausa con razón |
| `dropped` | Chris (cockpit) | descarte terminal con razón |

**Cockpit jamás cambia `refined/ready/developing/developed/reviewing/done`.** Si Chris intenta el endpoint responde 403:
```json
{
  "error": "transition_forbidden",
  "from": "ready",
  "to": "developing",
  "reason": "esta transition la ejecuta /dev-team. Invoca la skill desde Claude Code para arrancar el build."
}
```

---

## Override path (force-state)

Si Chris necesita forzar un state que no le pertenece (caso raro, ej. corregir un state mal asignado), debe hacerlo via Claude Code:

```
/pm-{sistema} <story-id> force-state <new-state>
```

`/pm-{sistema}` pide razón explícita + ratifica + escribe checkpoint.md con `force_state_reason: <texto>` + `force_state_by: chris` + `force_state_at: <timestamp>`. Auditor revisa estos casos al cierre del release.

**No hay endpoint cockpit para force-state.** Eso evita que un click accidental rompa el state-machine.

---

## Read-only fields en checkpoint cockpit

Fields que el cockpit muestra pero NO permite editar desde la UI:

| Field | Owner | Por qué read-only |
|---|---|---|
| `owner` (agente) | Claude (`/po-ux`/`/po`/`/ux-agentico`/`/architect`) | Determinado por análisis del scope |
| `type` (ui/service/agentic/bugfix) | Claude (al refinar) | Inferido de spec |
| `module` (ruta funcional) | Claude (al refinar) | Inferido de cap_target |
| `capability` (slug) | Claude (al refinar) | = `cap_target` o derivado |
| `surfaces` (BE/FE/AG) | Claude (`/architect`) | Determinado por scope técnico |
| `next_action` | Claude (auto-update post-skill) | Reflejo del estado del workflow |
| `cap_target` | Claude (al refinar) o Chris (al crear story manual) | Define scope · solo Chris puede preseed en `idea`, Claude ratifica en `refining` |
| `cap_change_type` | Claude (al refinar) | Determinado por scan prior-art + scope |
| `release` (al merge) | Auto-sync con release.yaml | El asignment story↔release pasa via drag en Roadmap, no editando este field |

---

## Editable Chris fields (vía cockpit UI)

| Field | Cómo se edita | Cuándo |
|---|---|---|
| `release` | Drag entre releases en vista Roadmap | en cualquier state ≤ refined (idea, refining, refined) |
| `priority` | Selector P0/P1/P2/P3 en drawer | en cualquier state |
| `goal` (seed) | Textarea en drawer · 1-3 líneas | en idea state (Chris pre-seed) |
| `anti` (seed) | Textarea en drawer · 1-3 líneas | en idea state |
| `reuse` (seed) | Textarea en drawer · 1-3 líneas | en idea state |
| `parked_reason` | Modal "Parquear" | al hacer transition `→ parked` |
| `dropped_reason` | Modal "Descartar" | al hacer transition `→ dropped` |

**Goal/anti/reuse seeds:** son el input Chris para que la skill /po-ux/po pueda producir spec con dirección. Chris escribe versión cruda · skill los procesa + estructura en `01-spec.md` durante refining.

---

## Permisos Chris en chris-input.md

| Sección | Permisos Chris |
|---|---|
| 💭 Notas | CRUD completo (agrega, edita propias entries, borra propias entries) |
| 📎 Referencias | CRUD completo (incluye upload de imgs vía `/api/refs/upload`) |
| 💬 Conversación | Solo APPEND (responde a Claude turns) · NO edita entries Claude post-hoc |

**Cockpit UI:** Notas + Refs tienen botones edit/delete inline. Conversación tiene textarea "Responder" al final + render read-only de entries anteriores.

---

## Permisos Chris en cap YAML

Chris puede editar cap YAMLs SOLO via cockpit "✚ Extender" modal o "+ Nueva story basada en cap" botón. Esto siempre dispara la creación de una story nueva con `cap_change_type` declarado. NUNCA edición directa del cap YAML.

**Editar scenarios[]/change_log manualmente está prohibido** (pre-commit hook + auditor flag). Para modificar un cap, crear story con cambio apropiado.

---

## Permisos Chris en release YAML

| Field | Permisos Chris |
|---|---|
| `name`, `description` | edit **solo si NO shipped** (Chris escribe el bloque de trabajo · botón ✏ Editar en Roadmap) |
| `target_date` | edit solo si NO shipped (Chris pone deadline cuando hay compromiso) |
| `order` | edit (drag para reordenar releases en Roadmap) |
| `stories[]` | edit via drag stories entre releases (solo si NO shipped) |
| `status` | NO edit (auto-recompute · `shipped` lo sella el flujo "Cerrar → shipped") |
| `shipped_date` | NO edit (auto-set al cerrar release) |
| `verified_by`, `verified_at`, `verification_note` | NO edit a mano (los sella el flujo "Cerrar → shipped" con el check de comportamiento) |
| `production_status`, `production_version`, `production_scheduled_at`, `deployed_at`, `release_branch` | NO edit (eje despliegue · futuro · lo escribirá el flujo "pase a producción") |
| `release_id` | NO edit (es PK funcional) |
| `sistema`, `created_at`, `created_by` | NO edit |

**Release `shipped` = inmutable.** El cockpit bloquea `PUT` (editar) y `DELETE` (archivar) sobre releases shipped → 403. Correcciones excepcionales solo vía `/pm-{sistema}`. Ver `docs/process/release-protocol.md` § 2 + § 5.

**Cerrar → shipped (gate de comportamiento):** el botón "Cerrar → shipped" del Roadmap abre un modal que (1) le da a Chris el prompt exacto para correr la prueba de integración + E2E smoke en Claude Code, y (2) exige un checkbox confirmando que dio verde sin romper lo anterior. Sin ese check, el endpoint no marca shipped. Ver release-protocol.md § 5.

**Pase a producción (futuro):** botón visible en releases shipped pero **deshabilitado** (próximamente). Eje despliegue separado del eje integración. Ver release-protocol.md § 6.

---

## Anti-patterns prohibidos

- ❌ Cockpit endpoint permite `developing → done` desde UI (debe ser 403)
- ❌ Cockpit edita field read-only (owner, type, module, etc.) silenciosamente
- ❌ `parked` o `dropped` sin razón documentada (cockpit valida ≥10 chars)
- ❌ Chris edita entry Claude del chris-input.md (rompe trazabilidad conversación)
- ❌ Chris edita scenarios[]/change_log de cap YAML manualmente (debe ser via story con cap_change_type)
- ❌ Force-state via cockpit endpoint (debe ser via `/pm-{sistema} force-state`)
- ❌ Cockpit permite drag de story `developing+` entre releases (debe estar bloqueado · state demasiado avanzado para reasignar)

---

## Referencias

- `docs/process/checkpoint-protocol.md` — schema completo checkpoint.md
- `docs/process/capability-protocol.md` — cap YAML edits flow
- `docs/process/chris-input-protocol.md` — chris-input edits flow
- `docs/process/release-protocol.md` — release YAML edits flow
- `tools/{workspace.repo_prefix}-cockpit/app/api/transition/route.ts` — endpoint enforce whitelist
- `.claude/rules/story-closure-gate.md` — state machine completo
