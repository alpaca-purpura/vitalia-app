# HANDOFF — Programa empleados-IA: retomar en sesión limpia

> **Para:** la próxima conversación (limpia). **Objetivo:** recorrer el programa empleados-IA en serio + actualizar lo necesario, **SIN forzar nada sobre el scaffold de Vitalia**.
> **Naturaleza:** doc de arranque (efímero) — se consume + se pliega al roadmap del programa una vez hecho el trabajo de abajo. **Origen:** sesión 2026-06-02 (cierre durable-flows L1).

---

## 1. TL;DR — dónde estamos (la foto honesta)

- **L1 (motor de flujos durables)** — ✅ DONE + `migrated` + live-verified (persist+resume real en Postgres). **Infra lista y EN PAUSA**: NO es huérfana (verificada, consumida por import en 5 grafos scaffold), pero **no tiene un consumidor de producto real todavía — y está bien.** Fue una inversión deliberada de cornerstone (el research designó "flujo durable como T2" = cornerstone de la fase B).
- **L2 (FlowCompiler/FlowDefinition/EP-19)** — 🎨 DISEÑADO, build **deferred** (no se construye sin un ejemplo concreto primero).
- **Vitalia** — 🚧 **en construcción, SIN acciones de negocio sólidas todavía.** Chris lo está construyendo a su ritmo. Los 5 grafos "cableados" a L1 (wizard, treatment_followup, lucas, comunify community/cohort) son **scaffold / stubs Slice-1** (nodos sin LLM real, rutas que no llaman al grafo).
- **Story `empleados-ia-auto-extension`** — 📦 ARCHIVADA (`docs/archive/2026/stories/...`); su SSoT se graduó a arquitectura (una user-story no es SSoT).

## 2. El insight clave (NO perderlo — es el corazón de esta retoma)

**Un flujo durable es un CAPSTONE de un dominio sólido, NO la próxima user-story.** Vive *encima* de las acciones de negocio (Plano 1) que compone; en el vacío no es nada. Por eso:

- **Orden correcto:** acciones sólidas de UN dominio → el flujo durable como **coronación** que las amarra (y de paso ejercita/pule L1) → **después** de 1-2 flujos concretos, L2 generaliza el patrón.
- **NO** construir L2 ahora (sería generalizar sin un solo ejemplo).
- **NO** forzar un flujo durable sobre el scaffold actual (no hay piso de acciones sólidas; sería construir media Vitalia y de paso tocar L1).
- **Error que ya cometí y corregí:** propuse "promover `treatment_followup` a vivo" — pero es scaffold, no se promueve lo que no está construido. No repetir.

## 3. Doctrina nueva (ya cementada esta sesión)

**"Una user-story NO es SSoT"** — `docs/process/learnings.md § 2026-06-02` + MEMORY `user-story-no-es-ssot`. → **NO encapsular el programa empleados-IA en una historia de usuario.** El conocimiento durable vive en arquitectura/core-modules/ADR; el roadmap vive en el outcome (ver §5).

## 4. Qué hace la próxima sesión (el trabajo, en orden)

1. **Pasada READ-ONLY `/pm-vitalia`** — mapear el estado **real** de los dominios/stories de Vitalia + su madurez (qué está sólido vs scaffold, qué acciones de negocio existen de verdad). **NO refinar, NO construir — solo mapear la realidad** (para no volver a suponer como con `treatment_followup`).
2. **Enriquecer el roadmap del programa** (el outcome `empleados-ia-auto-extension-platform.md`) con 3 secciones nuevas, **aterrizadas en los dominios reales de #1**:
   - **§ Estado-ahora** (L1 done / L2 diseñado-pausa / Vitalia en construcción + madurez por dominio).
   - **§ Insight capstone** (el del §2 de este handoff).
   - **§ Protocolo de retoma** — "cuando el dominio X tenga acciones sólidas verificadas live → volvé acá → su primer flujo durable es el capstone → `/pm-vitalia` lo refina → `/architect` lo arma hand-rolled sobre L1 → `/dev-team` → `/auditor` → live-verify DoD #37".
3. (Opcional) Detectar si alguna story de Vitalia está **desalineada** con la dirección empleados-IA.
4. **Chris sigue desarrollando Vitalia** a su ritmo; el hilo empleados-IA queda **mapeado + parqueado** (la claridad vive en el repo, no en la memoria de la IA que se resetea).

## 5. SSoT — hogares vivos (leer estos, NO la story archivada)

| Qué | Dónde |
|---|---|
| Visión / research | `docs/architecture/luana-platform/empleados-ia-research.md` |
| Diseño L2 (FlowCompiler/EP-19) | `docs/architecture/luana-platform/durable-flows-L2-design.md` |
| Decisión / paradigma | `ADR-013-empleados-ia-auto-extension.md` + `PARADIGM.md §5b` |
| **Roadmap del programa (items 1-5)** | `docs/product/outcomes/empleados-ia-auto-extension-platform.md` ← se enriquece en §4.2 |
| L1 contract (hecho) | `docs/core-modules/flows.md` + `core/luana-core-flows/CHANGELOG.md` |
| Story archivada (registro inmutable) | `docs/archive/2026/stories/empleados-ia-auto-extension/` |

## 6. Items abiertos (no perder)

- **Gap de proceso:** el roadmap de un **programa platform multi-story cross-brand** no tiene contenedor canónico (los `outcome` se deprecaron en la consolidación 4-ejes 2026-05-28, que es brand-scoped). Hoy el outcome cumple ese rol de facto. **Pendiente `/pm-luana`:** definir el hogar real (¿revivir outcome solo a nivel platform? ¿`program.md`? ¿sección del ADR?). NO bloquea la retoma.
- **Validators SSoT a corregir** (anotados en el `REVIEW-agentic.md` archivado): `v_downstream_comunify` cita `tests/modules/comunify/copilot/` (no existe) → real `tests/agentic_evals/workflows/`; `v_replay_safety -k` debe targetear el file (la colección whole-tree tiene errores pre-existentes).
- **Backlog propio de Vitalia** (independiente de empleados-IA, del MEMORY): story B `vitalia-fase2-lisa-doctores` (developing, desbloqueada), C (push squash a main: ci-parity Dockerfile + migración 021 BYTEA), D (mirror nicolify `/pm-luana`).
- **Pre-existente fuera de scope** (no tocar salvo story dedicada): `vitalia tests/unit/test_extensions_register_all.py::test_ep8_channel_adapters_count_three` (stale 3-vs-10, en HEAD).
- **Dev convenience:** el host `.venv` tiene `psycopg[binary]` instalado (gotcha #4, para correr lo durable nativo) — no está en `uv.lock`, es local. El `uv sync` DENTRO del container corrompe el lock (resuelve sin dev-deps) → NO commitear un `uv.lock` modificado por sync-en-container.

## 7. Estado git

`wip/vitalia @ ab8621e7` · `origin/main @ 4c69aad3` (intacto, NO tocar) · tree limpio (salvo ruido pre-existente cockpit/pnpm). 8 commits esta sesión: durable-flows L1 (T-flows-3/4/5) + cierre + archive + graduación SSoT + learning.

## 8. Prompt para pegar en la sesión nueva

> Retomemos el programa empleados-IA en serio. Leé primero `docs/architecture/luana-platform/empleados-ia-HANDOFF-next-session.md` (tiene todo: estado, el insight capstone, los SSoT, los items abiertos). Objetivo de hoy: (1) pasada **read-only** `/pm-vitalia` para mapear el estado REAL de los dominios de Vitalia + su madurez (sin tocar nada); (2) enriquecer el roadmap del programa (el outcome) con § Estado-ahora + § Insight-capstone + § Protocolo-de-retoma, aterrizado en esos dominios. **NO construir L2. NO forzar un flujo durable sobre scaffold. Una user-story NO es SSoT.** Al terminar, Chris sigue construyendo Vitalia con el hilo empleados-IA parqueado y mapeado.
