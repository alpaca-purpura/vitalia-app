# ADR-vitalia-008 — Dev-app live verification gate (DoD)

- **Status:** accepted
- **Date:** 2026-05-31
- **Owner:** /pm-vitalia
- **Ratificado por:** Chris
- **Contexto previo:** memoria `verification-real-not-200` · `docs/process/learnings.md:1237-1244` (caso lisa-marca 2026-05-29) · audit `docs/process/audits/2026-05-27-stories-sweep.md:214`

## Problema

El principio "verificación real ≠ HTTP 200" (ejercer la acción real + leer logs + confirmar efecto) ya está
ratificado y cementado como doctrina (`test-design-doctrine.md`). Pero **no era un gate**: la closure-gate
(`reviewing → done`) sólo exigía auditor APPROVED + merge + capability con ≥1 scenario + e2e_test. Esos e2e
pueden correr contra stack local **o** mockeado — nada obligaba a verificar contra el entorno real desplegado
(`dev-app.vitalialat.com`). Resultado real: la suite verde mockeada shippeó 3 bugs "LIVE" (lisa-marca).

La Definition of Done de Chris es: **una story/bugfix no está `done` hasta que la acción del usuario se ejerció
y validó contra dev-app**. Este ADR la vuelve enforce-able sin sobre-ingeniería.

## Decisión

Se agrega un gate liviano a `reviewing → done` para vitalia: la story debe declarar `dev_app_verified` en su
`checkpoint.md`. Un solo punto de enforcement (`/pm-vitalia merge`); sin hooks ni validators nuevos (se añaden
después sólo si se demuestra que se saltea — YAGNI).

### Campo en `{story}/checkpoint.md`

```yaml
dev_app_verified:
  required: true            # ver árbol de abajo
  evidence: |               # OBLIGATORIO sólo si required: true — 1-3 líneas honestas
    Ejercí PUT /lisa/marca/identidad (cambio arquetipo → Guardar) como dr.demo@vitalialat.com →
    HTTP 200 + fila persistida en personality_profiles (id=…) + copilot_trace_event OK en logs.
  # dev_app_verified_skip_reason: "<razón>"   # OBLIGATORIO sólo si required: false
```

### ¿Cuándo `required: true`? (árbol — reusa el idioma condicional de hipaa-lite)

```
¿La story crea/cambia una superficie que un USUARIO ALCANZA en dev-app
 (página FE navegable · endpoint que la UI llama · flujo agéntico)?
  └─ SÍ  → required: true   (default de ui-story y agentic-story)
  └─ NO  → ¿es interno puro? (refactor sin cambio observable · infra · migración-only ·
            doc · test-only · cambio de engine sin superficie brand)
           └─ SÍ → required: false + dev_app_verified_skip_reason: "<razón>"
           └─ DUDA → required: true   (ante la duda, se verifica)

bugfix  → SIEMPRE required: true (ya hereda repro-first + completion "en vivo" de lifecycle.md)
```

### Qué cuenta como `evidence` válida

- **La acción real del usuario ejercida** — sobre todo los writes (POST/PATCH/PUT/DELETE), autenticado con el
  harness real: `dr.demo@vitalialat.com` (owner tenant Sanaré) + `CLERK_TESTING_TOKEN_VITALIA`.
- **+ el efecto observado**: fila en DB / cambio de estado / log relevante (`copilot_trace_event`, etc.).
- Honesta y breve. **NO** se exigen screenshots ni schema rígido.

### Anti-patrón explícito (lo que NO es evidencia)

- ❌ "GET /ruta → 200" sobre un placeholder (el caso lisa-marca: 200 sobre tabla inexistente, el PUT real daba 405).
- ❌ e2e verde que **mockea el backend** (falso verde).
- ❌ `evidence` con una palabra ("ok", "funciona") sin acción ni efecto.

## Enforcement (un solo punto)

`/pm-vitalia` en el comando `merge` (`reviewing → done`): si `dev_app_verified.required: true` y `evidence`
está vacío/ausente → **REFUSE merge** + pedir la evidencia. Si `required: false` sin `skip_reason` → REFUSE.
El auditor (Phase D gherkin-matrix) puede señalarlo antes, pero el gate duro vive en el merge.

## Consecuencias

- **+** La DoD de Chris deja de ser doctrina y pasa a gate. Mata el "verde por vacío" y el "200 = funciona".
- **+** Liviano: 1 campo + 1 check. Cero infra nueva. Scope condicional → no fricciona refactors/migraciones.
- **−** `dev-app.vitalialat.com` corre desde laptop vía Cloudflare Tunnel (no staging production-grade). El gate
  valida *comportamiento real*, no *infra de producción*. Suficiente para la etapa actual.
- **Promotable:** principio cross-brand (cada marca con su dev-app). Marcar `promotable: candidate` a /pm-luana
  si nicolify/comunify lo adoptan — recién ahí subir a `.claude/rules/story-closure-gate.md`.

## Referencias

- `docs/process/lifecycle.md` § 4 (Definición de DONE) + § Tipos de story (bugfix)
- `.claude/rules/test-design-doctrine.md` § Verificación REAL
- `.claude/rules/story-closure-gate.md` Fase F (gate cross-brand — NO tocado por este ADR)
- `docs/process/learnings.md:1237-1244` — caso origen lisa-marca
- `vitalia/.claude/rules/hipaa-lite.md` — patrón condicional reusado
