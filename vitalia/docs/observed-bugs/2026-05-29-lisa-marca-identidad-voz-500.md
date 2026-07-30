# Observed bug — lisa/marca identidad + voz-y-tono 500 en dev-app

**Fecha:** 2026-05-29
**Reportado por:** Chris (sesión refinamiento `vitalia-stub-caps-scenario-backfill`)
**Severidad:** alta (sección user-facing rota en dev deployado)
**Scope:** FUERA de `vitalia-stub-caps-scenario-backfill` (los 20 caps NO incluyen lisa-marca). Pertenece a la story `vitalia-fase2-lisa-marca` (built, computa `partial`) o a un hotfix dedicado.
**ESTADO:** ✅ RESUELTO 2026-05-29 (hotfix aparte, ratificado Chris). Ver § Resolución.

## Resolución (2026-05-29)

Dos root causes encadenados (ambos arreglados):

1. **`ModuleNotFoundError: No module named 'luana_core_brand_studio'`** (marca_service.py:138).
   Causa: el venv del backend (`vitalia_backend_venv`, named volume) estaba **stale** — le faltaban
   engine packages agregados después de su último sync (`luana_core_brand_studio`, `luana_core_copilot`, …).
   El app booteaba (imports de boot presentes) pero los imports lazy 500eaban en runtime.
   Fix: `docker exec luana-dev-vitalia_backend_dev-1 bash -lc "cd /workspace && uv sync"` + restart backend.
   (debugging.md #12 — engine package not editable in venv.) **Acción env, no commit.**

2. **`UndefinedTableError: relation "personality_profiles" does not exist`** (marca_service.py:168 fallback).
   Causa: F2-S7 (migración 033) creó `vitalia_prohibited_phrases` (brand-local) pero NUNCA creó la tabla
   engine `personality_profiles` (modelo SSoT: `core/luana-core-brand-studio/.../personality_model.py`).
   El código lisa-marca se mergeó "LIVE" sin su esquema de DB → 500 garantizado en cualquier DB.
   Fix: migración idempotente `vitalia/backend/alembic/versions/034_f2_s7bis_personality_profiles_schema.py`
   (schema-mirror exception, backend-ddd.md) + `alembic upgrade head`. **Commit.**

Verificación: `GET /api/v1/lisa/marca/identity` → 200 · `GET /api/v1/lisa/marca/personality` → 200
(antes ambos 500). Idempotencia migración confirmada (re-run = no-op).

### Follow-ups (NO en este hotfix)
- ⚠️ **Riesgo infra recurrente:** el venv-volume del backend va stale cuando se agregan engine packages.
  Conviene que el Dockerfile/compose corra `uv sync` al boot, o documentar `make dev-vitalia` re-sync.
  (Afecta TODAS las features que usan engine packages — no solo lisa-marca.) → idea para infra story.
- Regression test formal (contract `/personality` 200 + assert tabla en schema) → en story lisa-marca.
- lisa-marca computa `partial` — esto era parte de por qué. Su backfill de scenarios queda para su propia story.

## Síntoma

En `https://dev-app.vitalialat.com/{tenant}/lisa/marca/identidad`:
> "No se pudo cargar la sección Identidad. API error 500"

En `https://dev-app.vitalialat.com/{tenant}/lisa/marca/voz-y-tono`:
> "No se pudo cargar la configuración de voz. Intenta de nuevo."

Tenant observado: `e69a691d-070e-5caf-a053-6e74642ec100`.

## Triage preliminar (no fix — solo pointer)

- BE endpoints implicados: `vitalia/backend/src/modules/vitalia/brand_studio/api/routers/marca_router.py` + `application/services/marca_service.py` + `voice_blocklist_service.py` + `voice_preview_service.py` + `api/dtos/marca_dtos.py`.
- FE hooks/api: `vitalia/frontend/src/features/lisa/hooks/{useIdentityAutosave,useVoicePreview,useVoiceBlocklist}.ts` + `api/{marca,marca-voice-api,marca-presence-api}.ts`.
- Hipótesis (a confirmar reproduciendo): 500 BE — posible DTO/serialización, data del tenant faltante (seed), o regresión de migración/columna. NO es FE (FE muestra el error de un 500 del backend).

## Relevancia para la story actual

Es la **prueba viva** del bar que Chris fijó: "verified-live" local ≠ funciona en dev-app. El sweep (T-2 de cockpit-live-reconciliation) marcó la ruta `/lisa/marca/presencia` como "✅ OK" (carga), pero las sub-secciones `identidad`/`voz-y-tono` 500ean. Un sweep de presencia-de-ruta NO captura un 500 dentro de una sub-sección.

## Próximo paso (decisión Chris)

- [ ] Opción A: log only — fix en la story `vitalia-fase2-lisa-marca` o hotfix dedicado (recomendado: no es de los 20).
- [ ] Opción B: triage + fix ahora como hotfix aparte (worktree/branch hotfix), antes de seguir el backfill.

## Reproducir

```bash
# Local
make dev-vitalia
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8002/api/v1/vitalia/brand-studio/marca/identidad -H "X-Tenant-ID: <tid>"
# Revisar log BE
docker logs luana-vitalia-backend-dev --tail 200 2>&1 | grep -iE 'marca|identidad|voice|500|traceback'
```
