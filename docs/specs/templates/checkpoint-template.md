# Checkpoint Template — Resume Protocol (v4 — Punto 4 2026-05-06)

> Cada story tiene SU `checkpoint.md`. Cualquier sesión nueva lee este archivo PRIMERO para saber dónde retomar.
> El skill que cierra cada handoff (`/pm`, `/po`, `/po-ux`, `/architect`, `/dev-team`, `/auditor`) actualiza `last_artifact` + `last_modified` manualmente al escribir el frontmatter. NO existe hook automático (el viejo `post-edit-checkpoint.sh` fue removido 2026-05-06 — lógica rota).

---
story_id: STORY_ID                                # match folder name

# Release entity (único contenedor temporal · ver lifecycle.md § 5)
release: F2                                       # release ID · ver {brand}/docs/product/releases/{id}.yaml

# Capability lineage (v2 cement 2026-05-27)
cap_target: lisa.marca                            # null si cap nueva sin nombre aún · sino slug existente o nuevo
cap_change_type: extend                           # new | fix | extend | derive (story type:bugfix → fix, o extend si completa cap)
parent_story: null                                # opcional · si story spawned desde otra done (parent.id)

state: refining                                   # 10 estados v4 — ver tabla abajo
phase_workflow: null                              # ⚠️ DEPRECADO (X6 · proceso v5) — plegado en 'phase' + las fases nombradas {G,R,C,D}. Histórico/interno, NO operator-facing. Vocabulario viva = 10 estados + {G,R,C,D}.
phase: null                                       # runtime phase (ej AWAIT_CHRIS_VERIFY en G · HANDOFF_TO_AUDITOR). distinto de phase_workflow
autonomous_mode: false                            # Chris opt-in explícito: true → G (Chris-verify) se SALTA, corre a /auditor sin pausa (story-closure-gate · proceso v5)
last_artifact: 01-spec.md                         # último archivo escrito
last_modified: 2026-05-06T15:23:00Z
next_action: "Chris ratifica spec → invocar /architect"
ratified_by_chris: false                          # true cuando spec + diseño ratificados
input_spec_signed: false                          # ★ /po-ux UI deep (cement 2026-06-03) — RONDA 1 (intención: dónde vive + mapa funcional + pantallas-borrador + dudas) firmada por Chris. Gate interno del refining; el cockpit lo pinta como ✍firma1
mockup_final_signed: false                        # ★ /po-ux UI deep — mockup FINAL firmado por Chris (estados+validaciones+microcopy+átomos finales) ANTES del GO a RONDA 2 (Gherkin). Cockpit ✍firma2
spawned_at: 2026-05-06T14:00:00Z
spawned_by: /pm
parallel_safe: true                               # ¿otra sesión puede tocar artefactos de esta story sin conflict?
blocked_reason: null
audit_iterations: 0                               # cap 4 → escala automática
defer_audit: false                                # escape valve story-closure-gate
defer_audit_reason: null
parked_reason: null                               # mandatory cuando state=parked (≥10 chars)
dropped_reason: null                              # mandatory cuando state=dropped (≥10 chars)
hotfix_metadata:                                  # opcional, hot-fix tickets (R26) + story type:bugfix (ADR-011 · repro_verified REQUIRED true antes de developing)
  repro_verified: false
  repro_command: null
  diagnosis_validates_handoff: null
# Definition of Done — Live verification (Critical Rule #37 · definition-of-done-live-verify.md)
dod_live_verified: false                          # true SOLO cuando Claude ejerció la acción real del usuario en dev-app + leyó logs + confirmó efecto. Verde de gates/build/GET-200 NO basta.
dod_env: null                                     # ej "make dev-app-{brand} → dev-app.{brand}lat.com (Chrome DevTools MCP)" o "localhost:300X"
dod_evidence: []                                  # [{action, observed, backend_log}] — writes ejercidos (POST/PATCH/PUT/DELETE) + efecto observado en DB/UI
dod_verified_at: null                             # YYYY-MM-DD
dod_live_verified_skip_reason: null               # solo si la story es config/docs/tooling puro (sin UI ni endpoint)
# Demo manual (Critical Rule #37 §5) — solo stories funcionales (demo_required: true)
demo_required: true                               # false para técnico puro (+ demo_skip_reason)
demo_skip_reason: null
# G · Chris-verify loop (proceso v5 · story-closure-gate) — el signoff de Chris vive ACÁ.
# Consolida el viejo demo_signoff: UN solo signoff, ANTES del auditor (en G, no en F).
chris_verify:
  required: true                                  # false sólo si autonomous_mode o bugfix sin pedido
  signoff:                                        # lo llena Chris tras ejercer el kit (demo-script.md + dev-app) live
    signed_by: null                               # "Chris" al firmar
    date: null                                    # YYYY-MM-DD
    result: null                                  # SATISFIED | SATISFIED_WITH_FOLLOWUPS | REJECTED
    notes: null
    open_items: []                                # [{item, severity, disposition}]
  rounds: []                                      # [{round, observacion, resolucion|→historia}] = allowlist de scope ratificado (lo lee el auditor)
reconciled: false                                 # /pm-{brand} → true en R (reconcile pre-auditor); el auditor lo LEE como precondición de B
---

## Estados v4 (10 macro)

| # | Estado | Significado | Owner | WIP cap |
|---|---|---|---|---|
| 1 | `idea` | Spark + research opcional. Puede nunca implementarse | Chris + `/pm` | ∞ |
| 2 | `refining` | Decompose stories + drafts spec/UX/agentic. Loop iterativo | `/pm` + `/po-ux`/`/po`/`/ux-agentico` | ≤ 3 |
| 3 | `refined` | Spec + UX/diseño ratificados Chris. Listo para architects | `/pm` cierra | ≤ 5 |
| 4 | `ready` | Paquete autocontenido completo (4 archivos canónicos) | `/architect` | ≤ 5 |
| 5 | `developing` | Autonomous build activo iterando vs validators | opencode/Sonnet/Opus (R23) | ≤ 3 |
| 6 | `developed` | Validators GREEN. Build cerrado, awaiting QA | `/dev-team` | ≤ 1 |
| 7 | `reviewing` | Auditor QA en curso (Opus C1-C3 + Sonnet tests) | `/auditor` | ≤ 1 |
| 8 | `done` | Auditor APPROVED + merge + capability promovida + docs | `/pm` | rolling 90d |
| 9 | `parked` | De-prioritized, NO abandonado | Chris | ∞ |
| 10 | `dropped` | Won't do (terminal) | Chris | ∞ |

## Phases — HISTÓRICO (X6-retired · proceso v5 · NO operator-facing)

> ⚠️ Las etiquetas de letra/`PHASE` (PM_DRAFT/PO_SPEC/UX_UI/…/AUDIT_T{n}/MERGE) quedaron **retiradas como operator-facing** (X6). La **vocabulario viva = 10 estados + las 4 fases nombradas {G,R,C,D}** (viven en el campo `phase`, NO en `phase_workflow`). Esta tabla queda como referencia interna del pipeline SDD — no la uses para razonar el estado de una story.

| Phase | Owner | Inputs | Output | Next |
|---|---|---|---|---|
| `PM_DRAFT` | /pm | opportunity / idea | `00-story.md` (opcional) | `PO_SPEC` |
| `PO_SPEC` | /po o /po-ux | `00-story.md` + spec template | `01-spec.md` + story YAML | `UX_UI` o `UX_AGENTIC` o `ARCHITECT` (según type) |
| `UX_UI` | /po-ux fusión | `01-spec.md` (ui-story) | wireframes inline en spec.md | `ARCHITECT` |
| `UX_AGENTIC` | /ux-agentico | `01-spec.md` (agentic-story) | `02-design-agentic.md` | `ARCHITECT` |
| `SPEC_RATIFIED` | Chris ratifica | spec + diseño | transition state=refining→refined | `ARCH` |
| `ARCH_DONE` | /architect | `01` + `02` | spawns architect-{be,fe,agentic} → `03-arch.md` + `04-validators.yaml` + `05-guidelines.md` + `06-tickets.yaml` | state=refined→ready |
| `BUILD_T{n}` | /dev-team | `06-tickets.yaml` | `T-{n}-impl-log.md` + `T-{n}-result.md` + push commit | next ticket O `BUILD_DONE` |
| `BUILD_DONE` | /dev-team | all validators GREEN | state=developing→developed | (Chris triggers /auditor) |
| `AUDIT_T{n}` | /auditor | `T-{n}-result.md` + tests | `T-{n}-review.md` (APPROVED \| CHANGES_REQUESTED) | next ticket O `MERGE` |
| `MERGE` | /pm | all tickets audit-passed + `CHECKPOINTS.md` | `07-merge.md` + apply diff to `product/` | `DONE` (state=reviewing→done) |
| `DONE` | (closed) | — | — | — |
| `BLOCKED` | any | — | escala Chris | resolver bloqueo |

## Bitácora

> Append-only. Cada agent que toca un artefacto logea aquí con timestamp.

- 2026-05-06 14:00 — /pm creó folder y checkpoint.md (state=refining)
- 2026-05-06 14:30 — /po redactó `01-spec.md`. Chris ratificó.
- 2026-05-06 15:23 — Spec ratificada → state=refined. En espera de /architect.

## Notas

- Si `parallel_safe=false`, otra sesión NO debe tocar artefactos hasta `next_action` complete.
- Si `blocked_reason != null`, ningún agent procede hasta Chris/PM resuelva.
- `audit_iterations >= 4` → escala automática a Chris (no más self-fix loops).
- Para hot-fix tickets (R26): `hotfix_metadata.repro_verified` MUST ser `true` antes spawn builder.

## Capability lineage (v2 cement 2026-05-27)

3 campos nuevos del frontmatter definen la relación story↔capability:

| Field | Significado | Valores válidos |
|---|---|---|
| `cap_target` | Slug del cap que esta story toca | string slug (ej `valeria-agenda`) · null solo si state=idea y Chris no decidió aún |
| `cap_change_type` | Qué tipo de cambio aplica al cap | `new` · `fix` · `extend` · `derive` |
| `parent_story` | Story padre (si esta story es spawned desde una done) | story_id o null |

### Decision matrix `cap_change_type`

| Situación | Valor |
|---|---|
| Cap NO existe · esta story lo crea | `new` |
| Cap existe · esta story arregla bug/regresión sin agregar funcionalidad | `fix` |
| Cap existe · esta story agrega scenarios nuevos al MISMO cap | `extend` |
| Cap existe · esta story crea cap hijo basado en uno existente (scope significativamente distinto) | `derive` (declarar `parent_story` opcional + cap YAML hijo tendrá `parent_cap`) |

### Validation enforce-able

- `/po-ux`/`/po`/`/ux-agentico` rechaza state=refining→refined si `cap_target` o `cap_change_type` ausentes
- `/architect` valida coherencia entre `cap_change_type` y archivos producidos (extend cita cap existente, derive crea YAML nuevo)
- Pre-commit hook rechaza checkpoint con cap_change_type fuera del enum {new, fix, extend, derive}
- Auditor Phase D verifica cap YAML target post-merge refleja `cap_change_type` declarado

Doc canónico: `docs/process/capability-protocol.md`.

## Release entity (v2 cement 2026-05-27)

Campo `release` es el único contenedor temporal del modelo (no hay outcome ni phase por encima). Ver `docs/process/lifecycle.md` § 1 + § 5.

Cuando esta story esté asignada a un release activo, su release_id debe existir en `{brand}/docs/product/releases/{id}.yaml`. Drag entre releases en cockpit Roadmap actualiza este field + la lista `stories[]` del release.

Doc canónico: `docs/process/release-protocol.md`.
