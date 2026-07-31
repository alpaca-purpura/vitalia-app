# Spec · § Mapa funcional + § Matriz de cobertura (capa humana del refinamiento)

> **Cement-date:** 2026-05-31. **Owner del proceso:** `/pm-{platform}`. **Decisión:** Chris ratificó Opción A
> (panorama humano + Gherkin juntos en `01-spec.md`, ligados por matriz). **Aplica a:** `/po-ux`, `/po`,
> `/ux-agentico` + template `docs/specs/templates/01-spec-template.md`. **Origen:** sesión 2026-05-31 —
> Chris pidió ver, en lenguaje humano, QUÉ se va a construir (happy path + bifurcaciones + reglas + criterios)
> sin tener que reconstruirlo desde el Gherkin, y con todo verificable.

## El problema que resuelve

El `01-spec.md` era **Gherkin-first**: abría directo en `SC-1..SC-N`. El Gherkin es excelente para la máquina
(mapea 1:1 a E2E) y para forzar precisión, pero es **mala lectura para un humano** que quiere el panorama:
el happy path queda disuelto en `SC-1`, las bifurcaciones desparramadas como lista plana (hay que reconstruir
el árbol mentalmente para detectar un caso faltante), y los criterios de aceptación se confunden con los scenarios.

Faltaba la **capa de comprensión + validación de completitud** ENCIMA del Gherkin.

## La doctrina: no compiten, viven a distinta altitud

| Capa | Lector | Qué es | Para qué |
|---|---|---|---|
| **§ Mapa funcional** | Chris (humano) | Happy path narrado + árbol de bifurcaciones + RN + AC | Comprender + validar completitud ANTES de construir |
| **§ Gherkin scenarios** | máquina / dev-team | `SC-N` Given/When/Then AI-resistant | Generar los E2E (sigue siendo la fuente de tests) |
| **§ Matriz de cobertura** | ambos | tabla branch/RN/AC → SC → verificación REAL | El puente: garantiza que nada quede sin prueba |

**No se autorean dos veces.** La prosa NO genera tests (no compite con Gherkin). El Gherkin NO se lee para
entender el panorama (no compite con la prosa). La matriz los liga por IDs (`Bif-N`, `RN-N`, `AC-N`), no por
duplicación de oraciones. Una sola fuente, dos lecturas.

## Estructura canónica de `01-spec.md` (Opción A)

```
§ Resumen ejecutivo

══ RONDA 1 · input-spec (intención) · ✍ FIRMA 1 (solo /po-ux · ver § Dos rondas) ══
§ Dónde vive                ← zona/caja (árbol paradigma) + shell + ruta del user
§ Mapa funcional            ← capa humana — ratifica Chris
   1. Happy path             → prosa numerada, camino dorado
   2. Bifurcaciones           → ÁRBOL: condición → resultado → [SC-N]
   3. Reglas de negocio       → RN-1..N (→ capability.business_rules)
   4. Criterios de aceptación → AC-1..N (checklist "listo cuando…")
§ Pantallas                 ← tabla de campos (NUEVOS vs EXISTENTES) — SIN mockup todavía (★ W0.5-bis)
§ Dudas abiertas            ← Chris las cierra ANTES del GO

══ (recién acá) MOCKUP creativo · ✍ FIRMA 2 = la firma FINAL única (★ W0.5-bis) ══
§ Mockup FINAL              ← shell completo + hoja + TODOS los campos conversados + TODOS los átomos
                              compone del design-system-canon · puede MEJORAR lo escrito · + estados + microcopy + graders
                              (actualiza § Mapa funcional si la forma cambió algo) → dispara RONDA 2

══ RONDA 2 · spec ejecutable · GENERADA al firmar · → refining→refined ══
§ Gherkin scenarios          ← GENERADO · cada SC con `Covers: [Bif-N, RN-N, AC-N]`
§ Matriz de cobertura        ← cada Bif/RN → ≥1 SC → verificación REAL
   + "Huecos detectados" + "SC huérfanos" (ambos = "ninguno" para pasar gate)
§ business rules + design-spec ← GENERADO (System design; resultado ≈ mockup)
```

## Dos rondas, dos firmas — UI deep refinement (★ cement 2026-06-03 · solo `/po-ux`)

> **Origen:** Chris pidió ser más profundo en historias con UI. El mismo `01-spec.md` se escribe + se firma
> en DOS rondas sobre el MISMO archivo (NO dos archivos — un solo SSoT). Atrapa errores ANTES de gastar en el Gherkin.
> **Aplica solo a `/po-ux` (UI).** `/po` y `/ux-agentico` mantienen la pasada única (el § Mapa funcional de arriba).
>
> **★ W0.5-bis (RATIFICADO Chris 2026-06-08):** invertido a **FUNCIONAL-PRIMERO / mockup-después** (hoy se generaba el
> mockup HTML de una vez → mal). Lo funcional se cementa en **viñetas humanas (NO Gherkin)** en un **doc vivo editable en
> el cockpit** (marcador acordado para los comentarios de Chris) ANTES de cualquier mockup. La **2ª firma es la única
> firma FINAL** (dispara Gherkin + architect). Cada pedido → `chris-input.md`. SSoT del método cross-tipo (los 3 sombreros
> PO/CTO/agéntico + intake conversacional + zero-loss + no-re-preguntar): **`harness-refactor-w0.5/REQ-TAKING-DETAIL.md`**.

**Flujo 6 pasos / 2 firmas (★ W0.5-bis · funcional-primero):**

1. **Conversar (intake)** — po-ux como **diseñador del sistema**: levanta qué/por qué + **dónde vive** (zona/caja) + **extiende-o-nuevo**; dice qué ya existe; **no acepta y ya, empuja**. Todo lo pedido → `chris-input.md`.
2. **Interrogatorio (gate duro)** — **1 pregunta a la vez · reflejo-primero · conciso · sin cave · viñetas humanas**. Camina: dato-por-campo (de dónde sale / entidad nueva o existente) · validación · estados (vacío/cargando/error/éxito) · roles/permisos (**el rol es obligatorio, con recomendación**) · qué pasa si falla + recuperación · edge cases · qué NO entra. Trae **referencias de internet**. Cementa lo FUNCIONAL. **Sin mockup todavía.**
3. **RONDA 1 (input-spec FUNCIONAL) · ✍ FIRMA 1** — § Dónde vive + § Mapa funcional (vistas/campos new-vs-existing/RN/AC en viñetas, **NO Gherkin**) + § Pantallas (tabla de campos, **sin mockup**) + § Dudas. Se escribe en el **doc vivo del cockpit** (marcador acordado para los comentarios de Chris). `checkpoint.input_spec_signed: true`.
4. **Mockup creativo (recién acá)** — la FORMA dentro del shell real (`SHELL-DESIGN-CONTRACT` de la marca) con **TODOS los campos conversados** + **TODOS los átomos**, **compone del design-system-canon**; po-ux es creativo y **puede mejorar lo escrito** (falta un átomo → se crea + queda en la base). Iterás la forma.
5. **Mockup final · ✍ FIRMA 2 = la firma FINAL única** — el mockup con TODO (estados + validaciones + microcopy + átomos finales); actualiza § Mapa funcional si la forma cambió algo. Lo que ves = lo que se programa. `checkpoint.mockup_final_signed: true`.
6. **GO → RONDA 2 (GENERADA)** — al firmar se **generan** § Gherkin + § Matriz + business rules + design-spec (System design; resultado ≈ mockup). transition `refining → refined`. (El **GO en vivo de Chris** post-build = fase **G**, aparte de estas firmas.)

**Por qué un solo archivo:** la RONDA 1 son las secciones humanas (arriba), la RONDA 2 las ejecutables (abajo).
La intención humana vive arriba del `01-spec.md` y sobrevive como el "porqué". NO se crea un `input-spec.md` aparte
(evita drift + un tipo de archivo nuevo). Las dos firmas son **gates internos del `refining`** — el estado NO cambia
hasta el GO de la RONDA 2.

**Disciplina de mockup:** antes de dibujar, po-ux declara la **zona/caja** (árbol de `paradigm-arquitectura.md`) →
de ahí sale el **shell**; lo toma del `{sistema}/docs/architecture/SHELL-DESIGN-CONTRACT.md` (si el shell no existe, se
genera con el design-system actual). El mockup vive DENTRO del shell, en la ruta donde el user aterriza, con **átomos
reales escogidos y nombrados** (`components/ui/` + `{design_system_ref.package}`) — disciplina D1 de `frontend-visual-fidelity.md`.
Esto garantiza "lo que veo = lo que se programa".

## Reglas duras (gate `/po-ux` y `/po`)

- **R1** — `§ Mapa funcional` presente con sus 4 sub-bloques (profundidad proporcional al tipo de story).
- **R2** — Cada `Bif-N` y cada `RN-N` mapea a ≥1 scenario en `§ Matriz de cobertura`. Hueco → STOP, NO `refined`.
- **R3** — Cada SC mapea a ≥1 ítem del mapa. SC huérfano → revisar scope creep.
- **R4** — La columna "Verificación" de la matriz es **REAL** (acción ejercida + efecto observado,
  NUNCA "GET 200"). Ver `.claude/rules/test-design-doctrine.md` § Verificación REAL.

## Proporcionalidad por tipo de story

| Tipo | Happy path | Bifurcaciones | RN | AC | Matriz |
|---|---|---|---|---|---|
| `ui-story` / `service-story` | obligatorio | obligatorio | obligatorio | obligatorio | obligatorio |
| `agentic-story` | turn-by-turn (en `02-design-agentic.md`) + branch tree en spec | obligatorio (ramas conversacionales) | obligatorio | obligatorio | obligatorio (→ evals) |
| `bugfix` (lite) | opcional | obligatorio (foco repro) | obligatorio | opcional | obligatorio (regresión) |

## Coherencia con la máquina existente (no inventa proceso nuevo)

1. **Cierra el loop idea→done.** La `§ Matriz de cobertura` es la **mitad delantera** del `gherkin-matrix.md`
   que el `/auditor` completa en Phase D (scenario → test path → status). El humano ve el mismo eje al
   principio, en lenguaje humano, antes de gastar en construir. La DoD live-verify (Critical Rule #37,
   `.claude/rules/definition-of-done-live-verify.md`) cierra el otro extremo: los scenarios declarados en
   la matriz DEBEN ser ejercidos en el stack real antes de `done` — no basta que el Gherkin esté verde en
   un entorno mockeado.
2. **Verificación REAL** (`test-design-doctrine.md`, cement 2026-05-29): la columna de verificación obliga a
   declarar la acción real + efecto, no un código HTTP.
3. **Eje Scenario** del modelo 4-ejes (`lifecycle.md`): el árbol + matriz son la vista humana de los scenarios
   que viven en la `capability`.
4. **Cockpit (filesystem-as-DB):** headers markdown + tablas se renderizan nativos → Chris ve el panorama en
   la conversación y en el cockpit, con el Gherkin un scroll abajo si lo quiere.

## Referencias

- `docs/specs/templates/01-spec-template.md` — template con las 2 secciones nuevas
- `.claude/skills/po-ux/SKILL.md` § Step 3 + Step 5 gate — owner UI std
- `.claude/skills/po/SKILL.md` § Step 3 — owner service/agentic spec
- `.claude/skills/ux-agentico/SKILL.md` § Step 2 — sincroniza turn-by-turn con el mapa
- `.claude/rules/test-design-doctrine.md` § Verificación REAL — la R4
- `.claude/skills/auditor/SKILL.md` Phase D — `gherkin-matrix.md` (mitad trasera del loop)
- `.claude/rules/definition-of-done-live-verify.md` — Critical Rule #37: los scenarios de la matriz deben ejercerse LIVE antes de `done`; la gherkin-matrix Phase D es la mitad trasera; el mapa funcional + matriz es la mitad delantera
- `.claude/rules/story-closure-gate.md` § Fase F/G — gate merge `reviewing → done` (exige `dod_evidence` + `chris_verify.signoff` firmado en **G** cuando `demo_required: true` · `demo_signoff` retirado/consolidado en proceso v5)
- `docs/process/capability-protocol.md` — `business_rules` (RN) viven en la cap
- `docs/process/lifecycle.md` — modelo 4-ejes (eje Scenario)
