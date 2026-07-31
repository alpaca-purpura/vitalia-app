# CIL — Continuous Improvement Ledger (4 carriles)

> **Estado:** SSoT vivo · **Owner:** `/pm-{platform}` (transversal `docs/process/`). **Origen:** proceso v5 §5.7 (HB-53), 2026-06-05. **Naturaleza:** el ÚNICO artefacto nuevo del proceso v5 — y **CONSOLIDA**, no agrega un tracker que compite. Es la **evolución** del `harness-backlog.md` ("eran solo notas y no trasladaban aprendizajes").
>
> **★ Es un ROUTER/índice, NO un 5º store.** Cada carril vive en su **hogar existente** (DIP — depende de la taxonomía de `learning-capture.md`, no la forkea). El CIL solo dice *dónde* vive cada tipo de aprendizaje + *cómo* se rutea + *cuándo* se homologa. **Cero archivo huérfano.**

## Por qué existe

El harness-backlog captura fricción sin trasladar el aprendizaje; los `learnings.md` per-story quedaban dispersos ("no hay dónde se acumulen"). El CIL es **un lugar donde se acumulan** los 4 tipos de mejora, cada uno cargando el aprendizaje (no solo la nota), homologados en el stop semanal `/harnesses-improvement`.

## Los 4 carriles (cada uno en su hogar existente — el CIL NO los reescribe)

| Carril | Qué | Hogar (SSoT real · NO duplicar acá) | Origen / alimentación |
|---|---|---|---|
| **L1 · harness** | proceso/tooling → reforzar skill/rule/agent/hook/template/cockpit | **`docs/process/harness-backlog.md`** (= L1 tipado · captura vía `/harness-issue`) | uso diario + auditoría |
| **L2 · producto / skills-arq** | aprendizaje de producto → skills/arquitectura/domain docs | **`docs/learnings/{date}-{slug}.md`** (técnico ≥2 sistemas) · **`{sistema}/docs/learnings/`** (negocio) · `docs/process/learnings.md` (process) — taxonomía de `learning-capture.md` | `L · story-closure` rutea |
| **L3 · deuda técnica** | deuda de código/infra pura | **`docs/process/tech-debt.md`** (registro liviano · append) | dev / auditor |
| **L4 · capability-desfasada** | caps con reglas viejas, hoy stale | **auto-detect** (no hand-written): `scripts/cap_doctor.py` + caps anteriores a su cement-date + survivors heredados del mutation gate (`scripts/mutation_gate.py` §5.6) | auto |

Cada **entrada** (en su hogar) CARGA el aprendizaje, no solo la nota:
```
problema → causa raíz → cómo se resolvió → acción de refuerzo → carril
```

## Alimentación — `L · story-closure` rutea al carril

Al cerrar una story (`reviewing → done`), `/pm-{sistema}` + `/auditor` rutean cada problema/aprendizaje detectado al carril correspondiente (relaja el `learnings.md` per-story a "un lugar donde se acumulen"):

- fricción de proceso/tooling → **L1** (`/harness-issue` → harness-backlog).
- aprendizaje de producto/arquitectura → **L2** (`learning-capture.md` path canónico).
- deuda de código/infra → **L3** (`docs/process/tech-debt.md`).
- cap stale detectada (cap_doctor / survivor heredado) → **L4** (auto, no se escribe a mano).

Esto cumple la regla de `learning-capture.md` (Trigger 3 auditor) + el invariante anti-isla: **ningún aprendizaje queda huérfano**.

## Stop semanal — ritual `/harnesses-improvement`

El ritual lee los 4 carriles, los muestra (reúsa el board `/harness` del cockpit · HB-26, extendido con badge de carril), Chris remedia + marca "anotado/aplicado". Para el barrido EXHAUSTIVO periódico (schemas CC, staleness, punteros rotos, overlap) el ritual invoca el workflow `harness-audit-2026` (`Workflow({name:'harness-audit-2026'})`) como su **deep-sweep**. SSoT del ritual: `.claude/skills/harnesses-improvement/SKILL.md`.

## Anti-patterns

- ❌ Escribir entradas L1 DENTRO de este doc (L1 vive en `harness-backlog.md` — acá solo se apunta).
- ❌ Forkear la taxonomía de `learning-capture.md` (L2 usa SUS paths canónicos · DIP).
- ❌ Escribir L4 a mano (es auto-detect: cap_doctor + cement-date + survivors heredados).
- ❌ Crear un 5º store de mejoras (el CIL CONSOLIDA — si te ves agregando un tracker nuevo, STOP).

## Referencias

- `docs/process/harness-backlog.md` — L1 (hogar real)
- `.claude/rules/learning-capture.md` — taxonomía L2 (el CIL depende de ella, no la duplica)
- `docs/process/tech-debt.md` — L3
- `scripts/cap_doctor.py` + `scripts/mutation_gate.py` — fuentes L4 (auto-detect)
- `.claude/skills/harnesses-improvement/SKILL.md` — el ritual (stop semanal + deep-sweep)
- `docs/process/process-coherence-v5-2026-06.md` §5.7 — diseño
- `docs/process/harness-lifecycle.md` — HLP (el CIL es su evolución)
