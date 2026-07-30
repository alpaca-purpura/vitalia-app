# Demo Script — {STORY_ID}

> **Critical Rule #37 §5 · `definition-of-done-live-verify.md`.** Guion de **product demo** para que Chris valide manualmente la story, paso a paso, contra el MISMO `dev-app` que usó el dev en la live-verify. En **lenguaje de usuario** (no técnico — sin curl/tokens/URLs internas). Derivado de los scenarios Gherkin de `01-spec.md`. Solo para stories `demo_required: true`.

## SETUP (estado inicial)

- **Entorno:** `make dev-app-{brand}` → `https://dev-app.{brand}lat.com` (o `localhost:300X` fallback)
- **Usuario de prueba:** `<dr.demo@{brand}lat.com>` (rol + tenant)
- **Datos previos a crear:** `<...>` (mismo estado que la live-verify del dev)

## HAPPY PATH (1 acción = 1 paso · resultado esperado inline)

1. `<acción de usuario en lenguaje natural>` → **esperado:** `<resultado visible>`
2. `<...>` → **esperado:** `<...>`
3. `<el write principal: guardar / crear / eliminar>` → **esperado:** toast OK + el valor persiste al recargar

## EDGE CASES (reglas de negocio negativas / límite)

- `<acción inválida>` → **esperado:** `<mensaje de error de negocio correcto>`
- `<caso límite>` → **esperado:** `<...>`

## TEARDOWN (si aplica)

- `<borrar datos de prueba creados>`

---

## Resultado (lo firma Chris en G)

> El signoff de la demo **NO vive acá** — vive en `checkpoint.md::chris_verify.signoff` (proceso v5:
> UN solo signoff, en la fase **G** `AWAIT_CHRIS_VERIFY`, ANTES del auditor; `demo_signoff` quedó
> retirado/consolidado). Chris ejerce este script en vivo (dev-app) y registra el resultado allí:
> `result ∈ {SATISFIED | SATISFIED_WITH_FOLLOWUPS | REJECTED}` + `notes` + `open_items`.

<!-- voseo-allowed: template de proceso interno, no user-facing -->
