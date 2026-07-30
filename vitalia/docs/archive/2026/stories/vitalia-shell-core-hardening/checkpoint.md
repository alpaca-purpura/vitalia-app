---
story_id: vitalia-shell-core-hardening
type: ui-story                          # umbrella de hardening del shell-chrome (cross-módulo, no bugfix lite)
title: Shell-core hardening — consolidación del chrome del shell-organism + lift a @luana/ui-kit

# Release entity (contenedor temporal · lifecycle.md § 5)
release: F3

# Programa cross-brand (no lo OWNea /pm-vitalia — lo referencia · owner /pm-luana)
program: design-system-homologation     # ADR-014 + design-system-inventory-best-of-best.md
program_adr: docs/architecture/luana-platform/ADR-014-design-system-homologation.md

# Capability lineage
cap_target: null                        # higiene + hardening cross-cap del shell-organism (chrome transversal)
cap_change_type: fix                    # consolida FIXES del chrome (precedente: shell-valeria-responsive + shell-nav-scroll-errors, ambos fix+null). El lift a @luana/ui-kit es cap-work de /pm-luana (core), no una cap vitalia — gate HB-34 no exige YAML para fix.
parent_story: null

state: done                             # ★ 2026-06-11 APPROVED (CHECKPOINTS C1-C5 PASS) + signoff Chris SATISFIED → merge /pm-vitalia + archive R2
phase: MERGED
done_at: 2026-06-11
merge_artifact: 07-merge.md
reconciled: true                        # R liviano ejecutado: RN-7 ~260→280 reconciliado en 01-spec + ledger matriz ✅ + rounds = allowlist auditor
dark_mode_in_scope: true                # ★ ratificado Chris 2026-06-10 ("Si, mételo") — supersede el out-of-scope del backbone
input_spec_signed: true                 # firma reconciliación 2026-06-10 (deltas dark/B1/race + herencia FIRMA 1 backbone)
mockup_final_signed: true               # herencia mockup firmado backbone ratificada + caveat behavior-fi re-confirmado
ratified_by_chris: true
ratified_visual_by_chris: true          # vía herencia (mockup backbone firmado 2026-06-06 + ratificación herencia 2026-06-10)
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-bugfix-shell-valeria-responsive/mockups/shell-valeria-states.html
last_artifact: 06-tickets.yaml
module: shell
cross_module_scope: [shell, clinics, crm]   # heredado del responsive (punto 7 N3 toca clinics+crm)
agent_owner: null                       # shell-organism transversal (no es de un agente)
map_zone: infraestructura               # superficie no-funcional del shell (wrapper)
last_modified: 2026-06-10T12:00:00-05:00

# ── Ready package (architect-autonomous-mode.md) ──
autonomous_mode_chain: [dev-team, auditor, pm-merge]
autonomous_mode_ratified_by: chris        # 2026-06-10 verbatim "arranca /architect y continúa hasta el done"
autonomous_mode_ratified_at: 2026-06-10T12:00:00-05:00
autonomous_mode_caps:
  max_iterations_per_ticket: 10
  max_audit_iterations: 3
  max_wall_clock_minutes: 120
  max_total_cost_usd: 6.00
  on_cap_exceeded: "state=blocked + escalate Chris"
# autonomous_mode HARD-false check: el único trigger (engine touch core/@luana/ui-kit) está MITIGADO
# (proposals accepted 256517a3 + 2026-06-01-lift-shell-organism + ratificación explícita Chris). Edits
# ui-kit acotados a additivo-mínimo (default = consumir N3 ya shipped v0.3.0). Pause-points en dispatch-plan.md.
ready_package:
  - 03-arch.md
  - 03-arch-fe.md
  - 04-validators.yaml
  - 05-guidelines.md
  - 06-tickets.yaml
  - dispatch-plan.md
# (ratified_by_chris arriba — forma + lift-timing + firma reconciliación, todo 2026-06-10)
parallel_safe: false                    # toca el shell mismo → colisión file-level con cualquier story del shell

# Naturaleza de verificación (DoD #37)
verification_nature: funcional          # chrome user-reachable → demo manual + anti-burbuja + live-verify
demo_required: true

# ── DoD #37 live-verify (ejercido 2026-06-10/11 · orchestrator) ──
dod_live_verified: true
dod_env: "localhost:3002 (stack dev real make dev-vitalia: FE+BE+cloudflared) — Playwright AUTENTICADO real-backend (Clerk dr.demo@vitalialat.com, fixture base.ts anti-burbuja: 0 pageerror/console-error//api≥400/Next-overlay). Chrome MCP no disponible esta sesión (server desconectado) — herramienta Playwright-autenticado es la 2ª válida per rule #37 (precedente embudo board-live)."
dod_evidence:
  - action: "Colapsar Valeria (botón propio) → strip 44px avatar → clic avatar reabre chat-only (collapse-strip-reopen.spec, autenticado, real-backend)"
    observed: "Strip 44px con avatar visible; reabrir → estado B sin historial; layout persiste; 0 errores consola"
    backend_log: "verify-no-backend-errors.sh vitalia ✅ sin ERROR/Traceback/Exception en la ventana 2026-06-11T03:05:18+"
  - action: "Abrir historial → EMPUJA 260px fijo (agente cede ancho), cerrar revierte (history-push.spec) + botón '+' limpia chat y archiva conversación al historial (new-conversation.spec)"
    observed: "Ancho agente C < B medido; historial 260px; '+' → chat vacío + ítem nuevo en lista historial (estado UI persistido en localStorage — el chrome no escribe DB por diseño; su efecto observable = DOM + persistencia + red limpia)"
    backend_log: "0 errores BE en ventana; requests /api proxied por rewrites nuevos → 2xx"
  - action: "Toggle dark en lisa/marca + adrian/inbox + mateo/agenda (dark-per-subtab.spec) + axe WCAG AA en dark"
    observed: "data-theme=dark activo, fondo NO blanco en shell NI contenido (mitad-clara MUERTA — BUG#2), axe 0 violations, toggle light revierte sin crash"
    backend_log: "0 errores BE"
  - action: "Soft-nav loop ×15 embudo→recuperar (next/link, band-aid revertido) + cross-tab lisa→adrian→mateo (soft-nav-loop.spec)"
    observed: "15/15 montajes sin 'Cargando shell' colgado, sin 'Rendered more hooks', sin Next overlay (B1 root-path MUERTO en el flujo verificado)"
    backend_log: "0 errores BE"
  - action: "N3: staff directorio + embudo workspace montan EntityWorkspaceLayout DE @luana/ui-kit (n3-list-detail.spec)"
    observed: "Workspace monta con EntitySubNavBar core; leafs disabled sin entidad (spec n3-directory-disabled, run suite completa)"
    backend_log: "0 errores BE (fetch entidades reales 2xx)"
verified_at: 2026-06-11T03:09:00Z

# ── chris_verify (ronda live de Chris 2026-06-11 — autonomous saltó G pero Chris probó = ronda de facto) ──
chris_verify:
  required: true
  signoff:
    by: Chris
    date: 2026-06-11
    result: SATISFIED
    verbatim: "ya quedó bien, continúa con el cierre hasta el done"
    notes: "2 rondas live ejercidas por Chris (colapso/gap + resize·wrap·historial-min) — ambas cerradas con root-cause + fix + verificación exhaustiva (68/68, matriz 22/22, escenarios exactos @1920 overhang 0). Ronda-allowlist para el auditor: push 280px (vs ~260 del spec), placeholder corto, pill container-query, min-w-72 header."
  rounds:
    - date: 2026-06-11
      reported_by: Chris
      issues:
        - "resize del chat de Valeria falla"
        - "al colapsar queda un espacio vacío (gap)"
        - "ampliación: historial expandido + TODOS los casos del resizer — en cualquier escenario debe verse bien"
      root_causes_found:
        - "react-resizable-panels v4 captura collapsible/collapsedSize en MOUNT — transición runtime inerte (panel quedaba 380px con strip adentro = gap 274px + drag muerto post-ciclo)"
        - "collapsedSize en unidades equivocadas (number=px en v4: stripPct 3.4375 era 3.4px, no 44px)"
        - "la persistencia del Group (useDefaultLayout) re-aplica el layout guardado pisando collapse()/defaultSize → retry rAF until-collapsed"
        - "RN-7 VIOLADA: el historial robaba 260px al chat (panel fijo, chat hasta ~58px) — el spec manda push real (panel se ensancha)"
      fixes:
        - "key-remount del Panel por estado + collapsedSize=44px + seam oculto en A (RN-9) + rAF retry collapse + push real ±histPct en flip de historyOpen con floor min+hist"
      verification: "matriz exhaustiva 22/22 PASS (estados A/B/C × drags crece/clamp/below-min × ciclos colapsar/reabrir × historial push × persistencia reload × viewports 1280/1100/800/round-trip · 0 errores consola) + spec permanente resizer-matrix.spec.ts 7/7 + no-regresión 25/25 (collapse-strip/default-30-70/history-push/drawer/resize-and-state)"
    - date: 2026-06-11
      reported_by: Chris (000.png + 001.png @1920)
      issues:
        - "resize al mínimo de Valeria (o descolapsar): contenido del chat RECORTADO (no re-wrappea)"
        - "historial abierto + drag del resize: el chat desaparece (~60px)"
      root_causes_found:
        - "grid-rows sin cols explícitas → columna implícita auto trackea al CONTENIDO (604px), ignora el contenedor → overflow-hidden recorta. Fix: grid-cols-[minmax(0,1fr)] + min-w-0"
        - "min del panel en C no incluía el historial (280px reales, no 260) → drag clampeaba al min de B y el historial se comía el chat. Fix: minSize efectivo dinámico + key remount B|C + retry rAF push"
        - "polish al mínimo: 'Valeria'→'V.' (min-w-72) · pill no cabía (container query @24rem) · placeholder 4 líneas (corto + title)"
      fixes:
        - "commit 1c339736 — 6 files"
      verification: "escenarios exactos de Chris @1920: overhang 0px ×3 (sin recorte, chat legible) + suite COMPLETA 68/68 (0 flaky) + resizer-matrix 7/7 con asserts anti-recorte + min-C permanentes"
autonomous_mode: true                   # ★ RATIFICADO Chris 2026-06-10 verbatim: "arranca /architect y continúa hasta el done" — corre architect→build→auditor→merge sin pausa G. El architect valida criterios HARD-false en dispatch-plan; si detecta uno, ESCALA a Chris en vez de proceder. Live-verify #37 + dod_evidence siguen obligatorios (autonomous no relaja el DoD).

# ─────────────────────────────────────────────────────────────
# Consolidación — qué absorbe esta umbrella (ratificado Chris 2026-06-10)
# ─────────────────────────────────────────────────────────────
consolidates:
  - story: vitalia-bugfix-shell-valeria-responsive
    prior_state: refined
    action: folded                      # parked + folded_into esta story
    carry_forward:                      # artefactos refined que NO se descartan — son el backbone del spec
      - vitalia/docs/product/stories/vitalia-bugfix-shell-valeria-responsive/01-spec.md   # spec v3, 2 firmas, mapa funcional + matriz
      - vitalia/docs/product/stories/vitalia-bugfix-shell-valeria-responsive/mockups/shell-valeria-states.html  # mockup FINAL firmado
    baseline_build:                     # v1 ya construida + live-verified — NO se re-hace
      - "614bfbd5 — rail default + 30/70 + tablet drawer (8 files, 146 shell unit tests green)"
      - "29451ef6 — mount Sonner Toaster (orphan shell fix)"
    scope_7_puntos: "responsive (rail collapsed default · 30/70 · tablet drawer≥1024) + quitar botón web/agéntico (P1) + tenant-dropdown pegado a la derecha (P2) + N3 EntityWorkspaceLayout port de nicolify (P7)"
  - story: vitalia-fase1-shell-layout-5050-race-fix
    prior_state: parked
    action: folded
    scope: "race hydration next/dynamic({ssr:false}) + useDefaultLayout restore + ResizeObserver minSize (SC-3 snap-up). 0.5-1d."
  - latent_bug: U3-splitter-board-squeeze
    source: vitalia-fase2-adrian-embudo (checkpoint ux_product_decision U3, OPEN_SEPARATE_STORY)
    scope: "Splitter chat 55% fijo castiga el board. Shell-level cross-cutting (mismo root que B1)."
  - latent_bug: B1-shell-ssr-false-softnav-hang
    source: vitalia-fase2-adrian-embudo (B1 root cause) + learning 2026-06-03-next16-softnav-redirect-rendered-more-hooks
    scope: "shell dynamic({ssr:false}) cuelga en soft-nav ('Rendered more hooks' Next 16.2.3). Band-aid hard-nav en recuperar; root cause latente en otros soft-navs. Fix durable: edge-redirect (middleware) o resolver el ssr:false del shell."
  - candidate: BUG2-dark-mode-half-applied
    source: vitalia/docs/observed-bugs/2026-06-04-shell-valeria-squeeze-plus-darkmode.md (BUG #2)
    scope: "inbox vt-* sin variante [data-theme=dark]. Token-audit. Conecta con ds-showcase R-1SRC (consolidar tokens globals.css) + drift --agent-mateo. Candidato a entrar como parte de la limpieza de tokens previa al lift."

linked_not_folded:
  - story: vitalia-ds-showcase
    relation: demonstrator-R-FID        # alimenta esta story (HTML fiel por construcción), NO se fusiona
    note: "Demuestra el mecanismo de fidelidad + define el best-of-best que el chrome debe cumplir post-lift."

excluded:                               # NO son shell-chrome — fuera del scope, documentado
  - vitalia-bugfix-caps-last-modified-duplicado  # higiene YAML de caps, no UI del shell
  - vitalia-fase2-lisa-doctores keystone regression  # bug de feature Lisa (NuevoIntegranteModal), crashea EN el shell pero no es chrome
  - "todas las stories agent-feature (adrian-*/camila-*/lucas-*/lisa-*/mateo-*/config-*)"  # VIVEN en (shell-organism) pero CONSUMEN el chrome, no lo construyen

# ─────────────────────────────────────────────────────────────
# Lift a core — lift-DURANTE (ratificado Chris 2026-06-10)
# ─────────────────────────────────────────────────────────────
core_lift:
  target: core/@luana/ui-kit            # v0.3.0 — YA existe (lift parcial: layout/ archetypes/)
  proposals_status: accepted            # promotion proposals del lift FE/shell aceptados 2026-06-06 (commit 256517a3)
  timing: lift-durante                  # /architect buildea el hardening apuntando a @luana/ui-kit; brands consumen
  rationale: "Evita rework-en-vitalia-y-después-lift (doble trabajo). nicolify ya espejea el shell → mirror cross-brand que anti-duplication manda lift a core."
  cross_brand_consumers: [vitalia, nicolify]
  governance: "El gate brand→core es de /pm-luana (promotion-protocol). /pm-vitalia entrega el hardening brand 'excelente' (funcional + técnico) + handoff proposal a /pm-luana. El sequencing final rework-vs-lift lo cierra /architect en `ready`."

# ─────────────────────────────────────────────────────────────
# Prior-art scan (anti-duplication-refining · Step prior-art-scan)
# ─────────────────────────────────────────────────────────────
prior_art_scan:
  engine: "core/@luana/ui-kit v0.3.0 EXISTE (src/layout, src/archetypes) — CONSUMIR/EXTENDER, no recrear. Es el target del lift."
  brands_live: "nicolify/.../(shell-organism) + nicolify/components/shared/shell-organism = port re-skinneado del shell de vitalia (mirror cross-brand)."
  learnings:
    - vitalia/docs/learnings/2026-06-06-n3-entity-workspace-layout-from-nicolify.md   # nicolify factorizó EntityWorkspaceLayout MEJOR que vitalia → adoptar al lift
    - docs/learnings/2026-06-03-next16-softnav-redirect-rendered-more-hooks.md         # root cause B1 (cross-brand)
    - vitalia/docs/learnings/2026-05-23-shell-layout-race-condition-defer.md           # race-fix
  decision: "EXTEND-ENGINE + LIFT. El chrome se endurece apuntando a @luana/ui-kit; se adopta la mejor factorización (EntityWorkspaceLayout de nicolify); se mata el mirror cross-brand."

# ─────────────────────────────────────────────────────────────
# Preconditions HARD antes del BUILD (Step 0 / story-closure-gate)
# ─────────────────────────────────────────────────────────────
build_preconditions:    # ★ GATE EJECUTADO 2026-06-10 (ratificado Chris, opción a)
  - "✅ vitalia-fase2-adrian-embudo → defer_audit: true (developed + dod_live_verified preservados; /auditor post-hardening evita re-audit por rebase del chrome crm)."
  - "✅ vitalia-fase2-lisa-doctores → parked (⚠️ keystone regresión /lisa/staff queda VIVA — bug de feature Lisa, NO chrome; primer trabajo post-hardening)."
  - "✅ Slot refining liberado: vitalia-fase2-lisa-servicios → parked (su N3 depende del contrato EntityWorkspaceLayout que este hardening cambia; firma 1 preservada). Refining queda {ds-showcase, config-cuenta} + slot libre para esta umbrella."
  - "⏳ Adquirir bucket locks code:{shell,clinics,crm} al arrancar el BUILD (no antes)."

next_action: >-
  ★ 2026-06-10 READY (/architect cerró ready package — 6 artefactos). Decisiones cerradas:
  A soft-nav = edge-redirect proxy.ts 307 + revertir band-aid hard-nav→next/link (ssr:false se conserva,
  root cause react-resizable-panels v4); B lift = el N3 YA está shipped en @luana/ui-kit v0.3.0 (core-ds-foundation)
  → CONSUMIR + migrar staff/embudo + retirar EntitySubNavBar brand-local (mata mirror); el chrome del shell NO se liftea
  acá (es el outcome platform 1-2 sem de 2026-06-01-lift-shell-organism → handoff /pm-luana); C dark = hardcoded→token
  (los --vitalia-* core YA tienen dark; reduce deuda, no wholesale). 8 tickets FE (builder-frontend/sonnet), autonomous_mode: true.
  PRÓXIMO: /dev-team vitalia vitalia-shell-core-hardening — adquirir locks code:{shell,clinics,crm} al arrancar
  build → T-1..T-8 → /auditor → G demo Chris (chris_verify.signoff HARD, gate #37 dod_evidence) → /pm-vitalia merge
  → handoff proposal /pm-luana (chrome listo para lift) → /auditor embudo (defer_audit) post-hardening.
  Pause-points (dispatch-plan.md): edit ui-kit no-additivo → STOP /pm-luana; bump Next → escalate Chris.
  NO arrancar build con otra story del shell en developing (parallel_safe=false).
---

# vitalia-shell-core-hardening — checkpoint

## Goal

Consolidar **todo el trabajo abierto del chrome del shell-organism** (responsive + race-fix + bugs latentes) en **un solo vehículo** para hacer **una sola revisión** de un shell **excelente — funcional y técnicamente (arquitectura + estructura de archivos limpias)** — y, durante ese hardening, **lift el chrome a `core/@luana/ui-kit`** para que vitalia + nicolify lo consuman (matar el mirror cross-brand).

Nace de la conversación con Chris (2026-06-10, `/pm-vitalia`): "agrupar todas las historias del shell en una sola para una revisión, y cuando esté excelente, promover al core". Forma ratificada: **hardening story + programa** (no mega-story SDD). Lift ratificado: **lift-durante**.

## Por qué umbrella y no mega-story SDD

Fundir responsive (refined, cross-módulo) + race-fix (parked) + ds-showcase (refining, otro programa) + 2 bugs en UNA story SDD cruzaría `[shell,clinics,crm]`, violaría el WIP cap y mezclaría madureces. En cambio esta umbrella:
- **Absorbe** el chrome puro (responsive + race-fix + U3 + B1 + token-audit) — ver `consolidates`.
- **Enchufa** al programa cross-brand `design-system-homologation` (ADR-014) que ya existe — no abre track paralelo.
- **Vincula** ds-showcase como demostrador R-FID (no lo funde).
- **Deja afuera** explícitamente lo que no es chrome (ver `excluded`).

## Contexto del lift (ya sancionado)

Los promotion proposals del lift FE/shell → `@luana/ui-kit` están **`accepted` desde 2026-06-06** (commit 256517a3). Chris ya pidió "cerrar las stories abiertas ANTES del lift (árbol limpio)". Esta umbrella **es el vehículo de ejecución de ese lift** — el responsive era su ruta crítica (única colisión file-level = el shell mismo). `@luana/ui-kit` ya está en v0.3.0 con lift parcial (layout/ archetypes/).

El gate brand→core es de **`/pm-luana`** (promotion-protocol). `/pm-vitalia` entrega el hardening brand "excelente" + handoff de proposal final. La decisión de sequencing rework-vs-lift la cierra `/architect` en `ready`.

## Estado de las stories absorbidas

| Story | Antes | Ahora | Artefactos preservados |
|---|---|---|---|
| `vitalia-bugfix-shell-valeria-responsive` | refined | **parked + folded_into** | 01-spec v3 (2 firmas) + mockup FINAL + baseline build (614bfbd5, 29451ef6) — backbone del spec |
| `vitalia-fase1-shell-layout-5050-race-fix` | parked | **folded_into** | approaches TBD + learning race-condition |
| U3 splitter / B1 ssr:false soft-nav | sin story | **capturados acá** | observed-bugs + learning Next16 |
| `vitalia-ds-showcase` | refining | **linked (demostrador)** | NO se funde — alimenta el best-of-best |

## Anti-objetivos

- NO descartar el baseline ya construido + live-verified del responsive (v1 puntos 3/5/tablet).
- NO recrear lo que ya vive en `@luana/ui-kit` — extender/consumir.
- NO arrastrar a la umbrella las stories agent-feature (consumen el chrome, no lo construyen).
- NO mergear sin demo Chris (G · chris_verify.signoff) + auditoría + dod_evidence live (#37).
- NO formalizar el lift sin handoff a `/pm-luana`.

## Referencias

- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` · `ADR-vitalia-004` (shell-feature) · `ADR-vitalia-006` (SSR-safe store) · `ADR-vitalia-003` (visual)
- `docs/architecture/luana-platform/ADR-014-design-system-homologation.md` + `design-system-inventory-best-of-best.md`
- `core/@luana/ui-kit` (v0.3.0 — target lift)
- promotion proposals lift FE/shell (accepted 2026-06-06, commit 256517a3)
