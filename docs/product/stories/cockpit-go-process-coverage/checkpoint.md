---
story_id: cockpit-go-process-coverage

# Platform tooling story (owner /pm-luana). Vehículo = HLP-lite (Harness Lifecycle Process):
# el cockpit es tooling cross-brand (tools/luana-cockpit-go), NO código de producto brand/core.
# Diseño/SSoT = tools/luana-cockpit-go/ROADMAP.md (no se duplica architect ready-package pesado).
# Gate entre fases = ratificación de Chris + live-verify en localhost:4002 (cockpit corriendo).
release: null                                     # tooling, no entra en releases de marca
cap_target: null                                  # tooling, no es capability de producto
cap_change_type: null
parent_story: null

state: developing
phase: P1
autonomous_mode: false                            # Chris ratifica entre fases (P0→P1→P2→P3)
last_artifact: scripts/cockpit-{up,daemon}.sh (pivote impl=alpaca · prenter-harness@aac6675)
last_modified: 2026-06-11
next_action: "RESIDUALES CERRADOS (ronda 4 · alpaca d539f84): story-create idea ✓ · regen on-demand ✓ · gherkin discovery ✓ — story COMPLETA, Chris ejerce @ :4002 y decide cierre (G→done)"
ratified_by_chris: true                           # plan + decisiones ratificados (sweep P0→P3 + warn-first)

# Decisiones ratificadas (2026-06-11)
decisions:
  build_scope: sweep P0→P3 (fase por fase, ratificación de Chris entre cada una)
  coherence_enforcement: warn-first (banner+badge, NO bloquea transición; endurecer a HARD post-confianza)

dod_live_verified: false
dod_env: "localhost:4002 (cockpit-go corriendo · make cockpit-up)"
dod_evidence: []
dod_verified_at: null
demo_required: true                               # tooling con UI — se ejerce en el cockpit corriendo
chris_verify:
  required: true
  signoff:
    signed_by: null
    date: null
    result: null
    notes: null
    open_items: []
  rounds: []
reconciled: false
---

## Qué es

Cerrar el gap del cockpit Go para que cubra el **proceso de desarrollo entero** (idea→done),
no features sueltas. Plan autoritativo + gap verificado-contra-código en `tools/luana-cockpit-go/ROADMAP.md`.

## Fases (ratificadas — sweep P0→P3)

| Fase | Objetivo | Effort | Estado |
|---|---|---|---|
| **P0** | Spine: crear-story · gate-G signoff+dod · lane 🔨 | ~26h | ✅ done (P0-1/2/3) |
| **P1** | Coherencia: drift code-scan real · bidireccional cap↔code · cap-doctor | ~22h | ✅ done (re-audit `7c7b8463`) |
| **P2** | Edición: file-editor · extend-cap · refs/upload · forms+validación+permisos | ~24h | ✅ done (`eb369f6c`) |
| **P3** | Inteligencia+UX: sitemap jerárquico · fix harness L1/L3/L4 · UX proceso v5 | ~28h | ✅ done (`eb369f6c`) — residual: gherkin-exec real (decisión §3 pendiente) |

## Bitácora

- 2026-06-11 — /pm-luana: revisión a detalle del cockpit Go (verificado contra main.go/parsers.go). Reconciliados 4 docs previos (MEJORAS "100% parity" = falso · DEEP-AUDIT "no drill-down" = stale) en `ROADMAP.md` autoritativo. Chris ratificó sweep P0→P3 + enforcement warn-first. Story abierta. state=developing phase=P0.
- 2026-06-11 — **P0-1 (story-create) ✅ build + live-verify**. `scaffold.go` + `handleStoryNew` (POST /api/story/new) + botón "+ Nueva story" en board. Live-verify @ :4112: POST → 303 /story · checkpoint.md+chris-input.md creados (R4, state=idea) · board lista · commit por pathspec (pre-commit pasó). Selftest forward-cleaned.

## P0 · Implementación (3 sub-fases, todas ✅)

**P0-1 (story-create):** scaffold.go + POST /api/story/new + botón "Nueva story" en board.
- Live-verified @ :4112: checkbox.md + chris-input.md creados (R4, state=idea) · commit por pathspec.
- Commit `60e4c921`.

**P0-2 (gate-G signoff):** writeCheckpointStructured (surgical YAML nested edit) + POST /api/chris-verify + parseChrisVerify.
- Resolvió: lossy `writeCheckpoint` usaba map rebuild (aplanaba `chris_verify:` multiline) → nueva función edita bloques quirúrgicamente.
- Live-verified @ :4113: chris_verify block written (signed_by/date/result) sin perder resto.
- Commit `bfcb2c3f`.

**P0-3 (sessions lane 🔨):** readSessionLocks + Story.Lane field + board template badge.
- Reads `.session-lock/*.lock`, mapea story-id → lane (sesión identifier).
- Board renderiza "🔨 lane" badge en cards developing.
- Live-verified @ :4113: badge visible en vitalia embudo story.
- Commit `bfcb2c3f`.

## P1 · Implementación (coherencia · 3/3 ✅ — RE-AUDITADO Fable 2026-06-11)

> ⚠️ **Re-audit:** la primera entrega de P1 (Haiku, commits `e61e1c18`+`228f28b6`) tenía
> 3 fallas serias con "live-verify" falso-verde (grep de headers server-side, no DOM/datos).
> Corregido en commit `7c7b8463`. Caso de libro de `verification-real-not-200`.

**Fallas encontradas en el re-audit:**
1. `/functionality` muerto al nacer: html/template escapaba el JSON inline como string
   literal (faltaba `template.JS`) → `capabilities.forEach` TypeError; JS snake_case vs
   JSON PascalCase (sin json tags). Paneles vacíos, cero linking.
2. cap-doctor doblemente roto: template rangeaba `IssuesByGroup` nunca pasado (body
   vacío) + los "G1-G6" eran gates INVENTADOS (capability_id format, slug...) — los
   canónicos HB-51 son otra cosa (header-resuelve, área-viva, hogar, paths, superseded, map).
3. drift con ~50 falsos positivos: grep naive ignoraba el resolver canónico (aliases,
   formas functional_area). Verdad canónica: vitalia HEALTHY, 0 drift.

**Implementación correcta (commit `7c7b8463`):**
- **Arquitectura**: el Go NO reimplementa gates — shellea `scripts/cap_doctor.py --json`
  (mismo SSoT que el pre-commit, G1-G9 + schema, cache TTL 60s). `/drift` y `/cap-doctor`
  derivan del report canónico (anti-duplication: un mirror Go driftearía).
- **P1-1 drift**: tab muestra los gates canónicos con drift + detalle. Vitalia: ✓ 0.
  Nicolify: 3 reales (1 G4 + 2 G6 deuda rebuild documentada).
- **P1-2 functionality**: `template.JS` + json tags + linking bidireccional REAL
  (cap→archivos y archivo→caps) + `resolveCodeRefs` port de las formas TIER 1 del
  resolver (cap_id · fa · fa-dashed · {module}.{fa} · module.slug · dir.stem).
- **P1-3 cap-doctor**: render del report real — 9 gate-cards G1-G9 + schema errors +
  health badge con paridad exacta vs `cap_doctor.py`.
- **Fixes de base** (afectaban todos los tabs): loader caps multi-doc YAML + line-scan
  fallback para YAML malformado → 75/75 caps (antes 63, salteaba 12 silenciosamente) ·
  `yamlStr` mata `fmt.Sprint(nil)=="<nil>"` · functional_area escalar soportado ·
  guard panic en scan de headers · `/cap` detail usa refs resueltos (valeria-agenda 0→82).

**Verificación real (no falso-verde):** JSON inline parseado en node (75 caps · 54 con
refs · 1158 archivos · 0 tokens sin resolver) · cap-doctor vitalia 9/9 verde = paridad
`cap_doctor.py` · nicolify 3 drift reales renderizados · 9 tabs 200 + story/cap detail.

## P2+P3 · Implementación (commit `eb369f6c` · sesión 2026-06-11 Fable)

**P2 (edición):** file-editor modal (GET/POST /api/file, whitelist artefactos, commit por
pathspec) · open-in-editor (/api/open) · refs upload+galería (/api/refs/*) · extend-cap
form en /cap (cap_target prefilled) · permisos: writeGuard localhost-only + transition
whitelist CHRIS_ALLOWED_TRANSITIONS (rule #31) con 403+"esto lo hace skill X" + razón
≥10 chars parked/dropped persistida.

**P3 (proceso v5 visible + UX):** story-detail tab **Proceso** (stepper idea→done con
G·R, panel gate G con signoff form, panel DoD con dod_evidence parseado, reconciled,
transitions como botones) · **Map jerárquico** (zona→caja→área→caps, join canónico por
functional_area, áreas live vacías ⚠G2, caps sin hogar G3/G6) · **Harness** L1 (70 HB
reales) + L3 + L4 cableado a cap_doctor · board con tooltips de estado/owner/WIP +
badges ⏳G/✓DoD + help modal v2 (flujo SDD v5 para onboarding dev) · roadmap con 9
releases + stories linkeadas.

**4 bugs críticos cazados ejercitando writes reales (selftest):**
1. `gitCommit` SIN pathspec → barría lo stageado de otras sesiones (sweep M15) en cada
   write del cockpit. 2. `writeCheckpoint` rebuild naive → aplastaba chris_verify/
   dod_evidence/comentarios en cada transition. 3. Releases no cargaban (YAML
   malformado → roadmap vacío silencioso). 4. scaffold `cap_change_type: new` sin cap
   YAML → cap-gate bloqueaba commits. Commits gated ahora VISIBLES (warning + razón).

## ★ PIVOTE 2026-06-11 (noche) — el cockpit canónico pasa a ser el binario ALPACA

Chris pidió revisión UX con Playwright ("se ve malísimo, replantea todo") y apuntó a
`../prenter-harness/`. Tour Playwright de ambos cockpits → veredicto: la UI del binario
alpaca (Go + Next.js estática embebida, ~9.3MB) es categóricamente superior a los
templates Go a mano (sidebar, kanban WIP caps, drawer tabs, dnd, toasts) y ya corre
PERFECTO contra el workspace luana (brands detectadas, board vitalia, releases, CIL 32).

**Gap analysis** → lo único que el Go-templates local tenía y alpaca no:
1. Proceso v5 en el drawer (stepper G·R + signoff gate G + DoD) — tipos modelados pero UI nunca los renderizaba + sin endpoint write.
2. Doctor leía key `gates` (schema viejo, G1-G6) vs `cap_gates` G1-G9 actual.

**Port ejecutado en prenter-harness (commit `aac6675`):** tab 🧭 Proceso (stepper +
signoff form + DoD + reconciled + banner "⏳ te espera") · POST /api/operator-verify
con edit QUIRÚRGICO del bloque chris_verify (preserva comentarios — lección del
writeCheckpoint lossy) · DoctorGates G1-G9 en /drift · fix cap_gates fallback.
Verificado live contra luana-vitalia: paridad G1-G9 exacta vs cap_doctor.py · signoff
ejercido VÍA UI REAL (Playwright force-click → form → toast → checkpoint escrito,
comentarios intactos) · 409 state≠developed · 400 result inválido.

**Wiring luana:** `scripts/cockpit-{up,daemon}.sh` con `COCKPIT_IMPL=auto|alpaca|legacy`
(auto=alpaca si el binario existe; legacy = tools/luana-cockpit-go como fallback).
Daemon :4002 corriendo impl=alpaca con default_brand=vitalia.

**⚠️ Sesión paralela en prenter-harness:** sus commits 38b361a (Fase 3 CLI multi-workspace)
+ aa94c68 barrieron mi working-tree (handlers_misc.go viajó en SU commit — sweep M15
cross-repo). Contenido correcto, provenance mezclada. El binario post-Fase 3 mantiene
el modo `-workspace -port` que usa el wiring luana (verificado).

## Ratificación Chris (2026-06-11 noche)

1. **Pivote alpaca RATIFICADO** — "este cockpit con Go es el final y único que usaré".
2. **Legacy PURGADO**: `tools/luana-cockpit-go/` (168 files, P0-P3 del día — git history
   lo preserva) + `tools/_legacy/luana-cockpit/` eliminados. Scripts cockpit-{up,daemon}.sh
   solo-alpaca (sin fallback), pidfile/log → `$WS/.cockpit/` (gitignored). CLAUDE.md
   § Tools actualizado.
3. **Backlog UX ratificado por Chris** (en curso, en prenter-harness):
   - Story drawer: demasiados tabs → simplificar agrupando lo técnico, forma de proceso,
     tooltips en TODA propiedad que necesite explicación (como el legacy).
   - Nav configurable: poder agregar/eliminar módulos/tabs/sub-tabs en el tiempo.
   - Map: va, con más detalle.
   - Dato de mapa vitalia: el panel admin está dentro de "configuración" y es un módulo
     separado → corregir SYSTEM-MAP + functional_area de caps admin-*.

## Ronda 2 UX (2026-06-11 noche · ejecutada post-ratificación) — TODO ✅

1. **Legacy purgado** (luana `c048747d`): tools/luana-cockpit-go + _legacy/luana-cockpit
   eliminados · scripts solo-alpaca · pidfile/log → `$WS/.cockpit/` · CLAUDE.md actualizado.
2. **Drawer simplificado** (alpaca `e03c090`): 10 tabs → 5 en forma de proceso
   (Proceso · Definición[Spec+Diseño] · Técnico[Arq/Validators/Tickets/Checkpoint/Files
   sub-pills] · Audit · Operador) · transitions del operador movidas al tab Proceso ·
   `field-tooltips.ts` con tooltip para TODA propiedad del checkpoint.
3. **Nav configurable** (alpaca `e03c090`): `cockpit.config.yaml::nav` en la raíz del
   workspace = qué tabs + orden; sin archivo = todos. Verificado live: subset
   [board,map,harness] → sidebar exacto. Archivo default auto-documentado commiteado
   en luana.
4. **Map**: MapView alpaca ya superior (zone-tree v2 + lente proceso + huérfanas +
   health banner) — verificado contra datos vitalia.
5. **Admin = módulo separado** (SYSTEM-MAP v2 zona plataforma): caja `admin` propia
   ("Panel admin · staff interno"), área `panel`; 5 caps movidas
   `configuracion.admin → admin.panel` + `map_box: admin`. Gates G1-G9 TODOS verdes
   post-move (cap-doctor healthy · drift 0).

## Ronda 3 (2026-06-11 noche · Go de Chris) — Arquitectura → Mapa ✅

Insight Chris: Arquitectura y Mapa leían el MISMO SYSTEM-MAP (dos proyecciones) →
una sola vista con drill-down progresivo (alpaca `4bbc33c`):
- **N0** mapa: barra "áreas live/total" por caja + stats en header + título "Mapa del producto".
- **N1** click en caja → BoxDetailDrawer: descripción + áreas/status/release + caps
  clickeables + flujos cross-agent filtrados a ESA caja + entities posee/consume.
- **N2** colapsables al pie: flujos completos (5) + data ownership (11).
- Tab Arquitectura retirado (/arquitectura → redirect /map) · **Mermaid MUERTO**
  (ratificado) · ArchitectureView eliminado. Verificado live Playwright.

## Ronda 4 (2026-06-11 noche · "dale en ese orden, los 3") — residuales CERRADOS ✅

Alpaca `d539f84` (+777 LOC), verificado live Playwright contra vitalia:
- **A · story-create idea**: POST /api/story/new + botón "+ Nueva story" en board.
  Scaffold checkpoint+operator-input juntos (R4), state=idea, cap null hasta refinar.
  Verificado: selftest creada vía UI → drawer abierto → limpiada.
- **B · regen on-demand**: POST /api/capabilities/regen + botón 🔄 en DoctorGates.
  Shellea los scripts python canónicos (venv del workspace) — cierra staleness entre
  edición y commit SIN mirror del resolver. Verificado: validated_at = momento del
  click (1.1s). Exit≠0 del validador = drift, no error.
- **C · gherkin discovery** (decisión ROADMAP §3 RESUELTA: NO ejecutar — cockpit
  lee-no-genera): GET /api/gherkin-status + pill 🥒 Escenarios en Definición.
  SC-N del spec joineados con el gherkin-matrix del auditor: badge verificación +
  gherkin expandible + comando copy-paste (playwright/vitest/pytest). Verificado:
  embudo 12 escenarios, 5 PASS del matrix.

**Story sin pendientes** — todo el plan original (P0-P3) + pivote alpaca + 4 rondas
UX cubiertos. Próximo: Chris ejerce y decide cierre.

## Known issues / deuda

- dod_evidence array parsing es placeholder (devuelve nil). Requiere yaml.v3 para YAML array robusto. Deferred P0-3 si hay tiempo.

## Notas de proceso

- HLP golden rule: "nunca editar harness mid-feature" — esto ES la feature de tooling dedicada (no edición sneaky). OK.
- Build directo en `tools/` (main session) — no aplica builder-backend/frontend (scoped a brand/core).
- Stories de marca abiertas en paralelo (embudo/config-cuenta/nicolify) = jurisdicción /pm-{brand}, no bloquean tooling.
