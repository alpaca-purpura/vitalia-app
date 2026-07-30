---
story_id: empleados-ia-auto-extension
created_at: 2026-06-01T16:00:00-05:00
last_modified: 2026-06-02T11:35:00-05:00
notes_count: 1
refs_count: 4
conversation_count: 7
---

<!-- voseo-allowed: cocina conversacional interna Chris↔Claude (no user-facing); registro coloquial + citas de pedidos de usuario -->

# chris-input.md · empleados-ia-auto-extension

> Cocina de la story (conversación + verdicts), separada de los outputs (`00-research.md` / `00-story.md`).
> Doc canónico: `docs/process/chris-input-protocol.md`.

## 💭 Notas

### 2026-06-01 (sesión 2026-05-31 → 06-01)

Visión de Chris, en sus palabras (resumen de la sesión):

- Software agentic donde **si el usuario pide algo que el sistema no hace, lo creamos** — el agente actúa como analista de sistemas + UX, propone, y tras confirmación construye; notifica y aparece funcional.
- El software es **usable sin el agente** (determinista) — el agente extiende, no es requisito.
- **Cada módulo = un puesto de trabajo orientado a proceso, con su "agente"** dueño de su área (Adrián=ventas/sales agent, Lucas=growth/marketing, etc.). Llevarlo a "vender empleados-IA".
- Base obligatoria = "Mi Clínica" (Lisa) + Configuración. Cadena de valor vendible: Atraer (Lucas) · Vender (Adrián) · Operar (Mateo) · Retener (Camila). Vendibles sueltos / combinados / packs.
- Cada agente hace cualquiera de las acciones (los tiers) sobre sus capacidades y/o las extiende; coordina con otros directo o vía la supervisora (lo que funcione mejor calidad/precio).
- La supervisora (Valeria/Luana) interpreta, conoce qué hace cada trabajador, organiza, y cada uno entrega; labores automatizables.
- Cross-brand: Nicolify vs Vitalia comparten ~60% de procesos, ~40% difiere (esperado).
- Disciplina: **principios SOLID** en el manejo del trabajo de los agentes.
- Esto **complementa** el paradigma previo (3 planos), no lo contradice. Sobre un **core con la lógica de negocio**.

## 📎 Referencias

- **📄 doc** · `docs/architecture/luana-platform/PARADIGM.md` (3 planos — doctrina que esto evoluciona)
- **📄 doc** · `docs/architecture/luana-platform/ADR-010-orquestacion-agentica.md`
- **📄 doc** · `vitalia/docs/architecture/SYSTEM-MAP.yaml` + `ADR-vitalia-005` (primera instancia: 3 zonas/12 cajas)
- **📚 learning-ref** · MEMORY `luana-empleados-ia-vision` (índice pointer-first del avance de esta sesión)

## 💬 Conversación

> Append-only · Verdict labels: ✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE.

### 2026-06-01 16:00 · 🤖 claude · `/pm-luana` · ✓ APLICADO
Story platform creada en `state: idea` bundleando toda la investigación + decisiones de la sesión 2026-05-31→06-01. Artefactos: `00-research.md` (SSoT: panorama en capas + estado del arte 2026 citado + 12 primitivas × tiers + router 2-niveles + flujo durable 1ª clase + coordinación 3-modos + SOLID + 4 casos borde como tests + grounding vitalia/HIPAA + trayectoria B→A), `00-story.md` (JTBD), `checkpoint.md`.

Decisiones cementadas y registradas: metáfora maestra (empleados-IA por puesto sobre un motor) · cross-brand 60/40 (Liskov) · coordinación 3-modos (coreografía espina / supervisora orquesta / handoff directo medido) · SOLID con ownership de construcción en el dueño (la supervisora reenvía intención, no construye) · flujo = unidad durable de 1ª clase · 4 refinamientos del estrés-test (read/write split · techo de core · verbos-sobre-objetos + T0 inteligente · separación de poderes).

**Falta tu decisión (§14 del research):** ¿promovemos a **ADR-platform** (evolución PARADIGM.md/ADR-010) + outcome + stories derivadas por marca [vía recomendada — el "reset" que pediste], o **refining directo**? Luego `/architect` arranca la implementación B→A por el spike del **motor de flujos durables** (cornerstone). NO toqué PARADIGM.md/ADR-010 ni nada de implementación todavía — eso es el siguiente paso que vos gatillás.

### 2026-06-01 17:30 · 🤖 claude · `/pm-luana` · ✓ APLICADO
Ratificaste vía **(a)**. Promoví el paradigma a nivel plataforma:
- **`ADR-013-empleados-ia-auto-extension.md`** (accepted) — cementa D1 motor auto-extensión (12 primitivas × 5 tiers + router 2-niveles + flywheel) · D2 flujo durable 1ª clase · D3 coordinación 3-modos · D4 SOLID + ownership · D5 producto-empleados-por-puesto + cross-brand 60/40 · D6 techo de core + separación de poderes. Extiende ADR-010 (no lo reescribe).
- **`docs/product/outcomes/empleados-ia-auto-extension-platform.md`** — outcome platform con el trabajo derivado como **handoffs** (spike flujos durables → /architect; stories por marca → /pm-vitalia + /pm-nicolify; read-models; entitlement).
- **`PARADIGM.md` §5b** + puntero en ADR-010 (Extended by ADR-013).

NO escribí stories de marca (eso es de los `/pm-{brand}` — anti-creep) ni nada de implementación. Próximo gatillo tuyo: `/architect` para el spike, o `/pm-{brand}` para instanciar. Ahora: commit por pathspec + reporte de sync con main.

### 2026-06-01T17:05 · 🤖 claude · `/pm-luana` · 💡 PROPONE
Chris pidió homologar vitalia/nicolify/comunify en skills/herramientas/aprendizajes + misma "visión técnica de producto" (cambiando solo lo propio de cada marca), sobre base SOLID, ANTES de entrar a Vitalia a aplicar el paradigma de historia de usuario (este outcome, ADR-013). Diagnóstico: el know-how técnico (59 skills + 45 rules + PARADIGM + ADR-013 + engine) YA es 1 sola fuente compartida por diseño del monorepo — no se duplica. Lo divergente es la INSTANCIACIÓN por marca: comunify sin vision.md/SYSTEM-MAP/design-system-skill; y patrones cross-brand (shell-feature ADR-vitalia-004, mockup-003, ssr-store-006) atrapados en ADRs LOCALES de vitalia que nicolify HEREDA (smell: acople marca→marca, viola DIP). Propuesta cementada en `docs/product/outcomes/tech-baseline-homologation-platform.md`: modelo 2 capas (baseline platform estable vs delta por marca tipo Liskov) + promover los ADRs cross-brand a platform individuales + adelgazar overlays + comunify a paridad. Ratificado por Chris: (1) ADRs platform individuales, (2) baseline primero→luego Vitalia, (3) incluir comunify. Cockpit per-worktree NO se toca (por diseño). Próximo paso: Fase 1 — abrir promotion proposals + handoff `/architect` para autorar los platform ADRs generalizados. NO ejecutado aún (espera arranque Fase 1).

### 2026-06-01T17:40 · 🤖 claude · `/pm-luana` · ✓ APLICADO
Chris distinguió dos cosas que se estaban mezclando: (A) la homologación cross-brand ("el modelo") vs (B) ESTA historia, que cimenta la base técnica del sistema agentico+autoescalable. Aclarado: son dos CAPAS distintas, ninguna incluye a la otra. B = el MOTOR (flujos durables cornerstone + árbol capacidades + read-models + router 2-niveles, en core/ brand-agnostic) = la base técnica real. A = doctrina build-time compartida (promover ADRs FE/shell a platform + comunify paridad) = higiene de distribución, NO el cimiento. Consecuencia que invierte lo ratificado antes: B no depende de A, y Vitalia (marca referencia, ya tiene los patrones) tampoco necesita A previa. Orden RATIFICADO por Chris: **B (motor) → Vitalia (instanciar+validar) → A (homologar lo ya validado + comunify paridad) → nicolify/comunify (replicar)**. A pasa de "baseline primero" a "gate de replicación post-Vitalia" — así se promueve doctrina validada, no adivinada, sin repetir. Aplicado: `outcomes/tech-baseline-homologation-platform.md` actualizado (frontmatter `sequencing` + `depends_on: empleados-ia-auto-extension` + § Secuencia revisada). Próximo paso = arrancar B: spike motor de flujos durables (/architect platform) o mover esta story idea→refining.

### 2026-06-02T11:10 · 🤖 claude · `/pm-luana` · ⚠️ DUDA
Chris (sesión nueva post-`/clear`) preguntó: ¿implementamos la visión de la story con investigación profunda (empleados-IA)? ¿el core está cimentado para arrancar implementaciones en vitalia con `/pm-vitalia`? Levantamiento de estado **verificado contra archivos reales** (no solo memoria):
- **¿Implementada? NO.** Lo que existe es DIRECCIÓN ratificada (docs), CERO código. Story sigue `state: idea`. `git log` de la story/ADR = solo commits docs (`8474745c` ADR-013 + harness). `00-research.md` (SSoT, 22KB) + ADR-013 (`accepted`, pero Implementation state explícito: "stories aún en idea, derivadas NO arrancaron") + outcome-platform (`accepted`) + `PARADIGM.md` §5b. NINGUNA story derivada creada en ninguna marca (grep vacío).
- **Core "Fase B" (el motor) = NO existe.** Grep en `core/` de durable-workflow / capability-tree / intent-router / agent-skill-os / self-extension / flujos-durables = **vacío**. Los 26 packages son el engine ESTÁTICO de ADR-010 (events/outbox = espina de coreografía, extension-sdk EP-1..18 = "sobre" de T2, copilot, sales-agent, scheduling, iam…) + vitalia SYSTEM-MAP (registros del router L1 YA existen). Eso es el SUSTRATO, no el motor de auto-extensión.
- **Choque con `/pm-vitalia` directo:** según TU PROPIO orden ratificado (entry 17:40 de este mismo chris-input) — **B (motor) → Vitalia → A → replicar** — el siguiente paso NO es `/pm-vitalia` sino **B**: spike del motor de flujos durables vía `/architect` (platform), cornerstone de B. Ir directo a vitalia salta el cimiento que vos secuenciaste primero.

Te dejo la decisión de cómo proceder (sin auto-encadenar, porque la ruta que insinuás —`/pm-vitalia`— saltaría B). Nota lateral: story de marca `vitalia-fase2-lisa-doctores` sigue en `developing` (gate de cierre vitalia, ajeno a esto).

### 2026-06-02T11:12 · 🤖 claude · `/pm-luana` · ✓ APLICADO
Elegiste **arrancar Fase B**. Aplicado: checkpoint `state: idea→refining` (`phase_workflow: ARCHITECT_SPIKE_DURABLE_FLOWS`) + bitácora. Handoff inline a **`/architect` (platform)** para el **spike del motor de flujos durables** = cornerstone de B: decidir **Cloudflare Dynamic Workflows vs Temporal vs LangGraph+durabilidad** como EP T2 de composición de flujos durables, brand-agnostic en `core/`. Input del architect: `00-research.md` (§ stack 2026 + flujo durable 1ª clase + B→A), `ADR-013` (D2), `outcome` (tabla trabajo derivado #1). Respeta tu orden ratificado **B→Vitalia→A→replicar** — Vitalia (`/pm-vitalia`) queda detrás del motor.

### 2026-06-02T11:18 · 🤖 claude · `/architect` · 💡 PROPONE
Spike del motor de flujos durables (cornerstone B) producido y verificado: `spike-durable-flows.md`. Research date-aware (2026-06-02, WebSearch + WebFetch docs canónicas — todo post-cutoff verificado live).
**RECOMENDACIÓN:** **LangGraph durable execution** (`AsyncPostgresSaver`, paquete `langgraph-checkpoint-postgres`) como motor base, agregando durabilidad **DEBAJO** del supervisor LangGraph que ya usamos (no lo reemplaza). **Temporal** = puerta de escape documentada (lift futuro `/pm-luana` si hace falta durabilidad cross-service de días/años). **Cloudflare Dynamic Workflows DESCARTADO** (TS-only + requiere runtime Cloudflare Workers → rompe "un solo motor en `core/` Python").
**Hallazgo clave (NO-NEW-LAYER audit con greps):** hoy NO existe checkpointer durable LangGraph (0 matches `AsyncPostgresSaver`); `luana-core-events/outbox` es coreografía de evento único (sin replay multi-paso); `agent_state_checkpoint_model` es estado per-conversación custom. ⇒ el `FlowCompiler`+`FlowDefinition` es **net-new legítimo en `core/`** (no layer paralelo), reusando outbox+idempotency+observability+compliance+Extension SDK.
El doc trae el boceto del contrato EP T2 (FlowDefinition declarativo), el riesgo estrella (replay re-ejecuta nodos → idempotencia obligatoria, mitigada con `luana-core-idempotency`), y **5 preguntas abiertas que necesitan tu decisión** (§8): confirmar LangGraph base · EP-19 nuevo vs ensanchar EP-4 · primer flujo real = vitalia auto-liberación-cupos · bump `langgraph>=0.4` (= lift cross-engine que toca copilot+sales_agent en cada marca) · read-models antes/en-paralelo. NO se tocó código ni `core/luana-core-*/src/`, NO se transicionó a `ready` (es spike). State sigue `refining`.

### 2026-06-02T11:35 · 🤖 claude · `/pm-luana` · ⚠️ DUDA
Chris CONFIRMÓ la recomendación (LangGraph durable base) + ordenó flujo EXCEPCIONAL: arrancar la story del motor + mapear TODA la deuda + resolverla en esta misma conversación, **cero deuda para ninguna marca**, todo acá, sin diferir nuevas stories.
Levanté el **drift map real** (greps 2026-06-02) y actualicé `spike-durable-flows.md §Bitácora`:
- **Deuda concreta = "patrón D10":** 5 grafos durables YA construidos compilando con `checkpointer=` pero sobre `MemorySaver` (paquete `langgraph-checkpoint-postgres` nunca instalado). **vitalia ×3** (lucas_daily_analysis, wizard_onboarding, treatment_followup) + **comunify ×2** (community_engagement, cohort_enrollment). nicolify/lupulo = 0 (esqueletos).
- 3 engine pkgs en `langgraph>=0.2` (copilot, sales-agent, brand-studio). `AsyncPostgresSaver` = 0 imports reales.
- **Matiz que baja el riesgo:** `langgraph-checkpoint-postgres` es compatible con 0.2 → resolver la deuda NO exige el bump a 0.4 (separable).
- **2 capas:** **L1** = un-defer del checkpointer real (deuda concreta cross-brand, bounded, live-verificable) · **L2** = FlowCompiler/EP-19 compositor declarativo (feature net-new sobre L1).
Antes de spawnar un build de este tamaño (3 engine pkgs + 2 marcas + migraciones + downstream regression + live-verify), te pido confirmar el ALCANCE de "cimiento sin deuda esta conversación" — porque L1 es honestamente cerrable+verificable hoy, y el build completo de L2 cross-brand NO se puede declarar "done" honesto en una sola sesión (tu propia rule #37). State sigue `refining`.

### 2026-06-02T12:35 · 🤖 claude · `/pm-luana` · ✓ APLICADO
Elegiste **L1 completo + L2 diseñado**. Ejecutado en cadena:
1. **Gobernanza:** proposal `2026-06-02-durable-flows-engine.md` (`state: accepted`) autoriza editar `core/` para L1 (sin esto auditor-downstream-regression = FAIL) + outcome actualizado con split L1/L2 + drift map.
2. **Ready-package** (`/architect` platform, single-shot, verificado): `03-arch.md` (+ `-agentic`/`-be`) + `04-validators.yaml` + `05-guidelines.md` + `06-tickets.yaml` + `dispatch-plan.md`. Story `refining → ready`.
   - **Decisión hogar:** NUEVO paquete `core/luana-core-flows` (L2 lo necesita + aísla la dep pesada).
   - **★ Refinamiento material (baja el riesgo a casi cero):** **L1 NO requiere NINGÚN bump de langgraph** — el `uv.lock` YA resuelve langgraph 1.2.0 / langgraph-checkpoint 4.1.0; `langgraph-checkpoint-postgres 3.1.0` es compatible directo (los `>=0.2` eran floors, no ceilings). El riesgo cross-engine que me preocupaba se evapora.
   - **Anti-dup:** el factory brand-mirror (`wizard_checkpoint_config.py` + equiv comunify) se BORRA y se lifta a `make_durable_checkpointer` en core (era dead swap surface, nunca invocado en prod).
   - DAG L1 secuencial: T-flows-1 scaffold (Sonnet) → T-2 provider (Opus, R23) → T-3 wire 5 grafos + delete mirror (Opus) → T-4 migraciones idempotentes (Sonnet) → T-5 downstream regression + live-verify DoD #37 (Opus). L2 (FlowCompiler/EP-19) = `deferred-next-story`.
   - Open questions O-4/O-5 (primer flujo / read-models) = Chris-decision NON-blocking L1.
3. **Próximo (este turno):** handoff `/dev-team` (platform) para construir el DAG L1 completo → auditor → live-verify. Objetivo: cero stub "AsyncPostgresSaver pending" en ninguna marca al cierre.

### 2026-06-02T12:45 · 🤖 claude · `/dev-team` · ⚠️ DUDA
**T-flows-1 (scaffold) construido + integrado + verificado en `wip/vitalia`** (`c8551ed7` paquete + `1b2d9ab5` result): `core/luana-core-flows` (pyproject + __init__ + conftest) tracked, registrado en root pyproject (members 27→28), `langgraph` SIN bump confirmado, `langgraph-checkpoint-postgres` resuelto. Builder corrió sus gates GREEN.
**★ Snag estructural detectado + resuelto:** la Agent-tool aisló al builder en un **worktree propio brancheado de `main`** (no de `wip/vitalia`) y commiteó ahí. Eso rompe el modelo single-hub + el DAG secuencial: T-flows-2..5 brancheados de main NO verían el trabajo del ticket anterior. **Acción:** cherry-pické los 2 commits a `wip/vitalia` + eliminé el worktree aislado (local+remote). **Corrección de approach:** los tickets restantes (provider + wire 5 grafos + migraciones + downstream regression + live-verify) los construyo **in-place** sobre `wip/vitalia` (yo, Opus → R23 satisfecho para agentic production), NO vía sub-builders aislados.
**Estado honesto del esfuerzo:** cimiento sólido + T-flows-1 done. Lo que falta de L1 (T-flows-2..5) es grande + el live-verify (DoD #37) necesita el dev-stack docker levantado. Antes de seguir quemando en el build in-place completo, te confirmo el approach + el alcance del cierre de hoy.

### 2026-06-02T13:30 · 🤖 claude · `/dev-team` · ✓ APLICADO
**T-flows-2 (provider engine) DONE + commiteado** (`SCOPE_GATE_SKIP` + razón, platform story sobre hub vitalia): `core/luana-core-flows/checkpointer/` con `make_durable_checkpointer` (AsyncPostgresSaver pooled + EncryptedSerializer PHI + import diferido + nunca MemorySaver) + `build_flow_thread_id`/`build_phi_flow_thread_id`. **13 unit tests GREEN**, lint+format clean. **Correcciones honestas vs el ready-package:** (1) langgraph-checkpoint-postgres 3.1.0 usa nombres de tabla FIJOS → NO hay `table_prefix`; aislamiento = DB-por-marca (dsn) + tenant en thread_id. (2) psycopg sin libpq nativo → import diferido obligatorio + integración/live-verify necesitan `psycopg[binary]` o el contenedor.
**Mapeo real de T-flows-3 (más intrincado que lo scopeado):** los composition roots reciben el checkpointer por DI; `build_production_checkpointer` está **definido + exportado pero NUNCA llamado** (dead code) → la durabilidad de producción NUNCA se cableó: `lucas/application/services/__init__.py:91` construye con `_MemorySaver()`, y los cron handlers (vitalia+comunify) esperan un checkpointer de un worker ARQ que hoy no construye uno durable. Cablear bien = volver async el factory de lucas + propagarlo al cron job + cablear el lifespan de los workers ARQ por marca. Es trabajo cuidadoso multi-archivo cross-brand cuya verificación REAL necesita libpq+Postgres (= el gate live-verify). Te pongo el cuadro completo + recomendación antes de seguir.

### 2026-06-02T13:45 · 🤖 claude · `/pm-luana` · ✓ APLICADO
Chris pidió **handoff + prompt para sesión fresca**. Aplicado: escribí `HANDOFF-L1-build.md` (SSoT del traspaso) con lo done+committed (gobernanza + ready-package + T-flows-1 + T-flows-2, wip/vitalia @ 98006df8), el trabajo restante (T-flows-3 wire+delete mirror / T-flows-4 migraciones / T-flows-5 downstream+live-verify), los **6 gotchas** que costaron tiempo (sub-builders se aíslan en worktree → construir in-place; scope-gate SKIP para core/; venv compartido; libpq/psycopg[binary]; table_prefix N/A; comunify dev-app bug → live-verify en vitalia), el mapeo real del wiring (dead factory → lifespan ARQ async por marca), los validators y las reglas vigentes. Checkpoint next_action apunta al handoff. Commit docs + push. Entrego el prompt copy-paste para arrancar la sesión fresca que cierra L1 cero-deuda → auditor → /pm-luana close.
