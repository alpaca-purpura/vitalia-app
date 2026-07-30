---
title: "Verificación live de auth con JWT real de Clerk (god-matrix mint pattern)"
date: 2026-05-30
type: technical
brands_affected: [vitalia, nicolify, comunify, lupulo]
brand: vitalia
origen: "story vitalia-iam-slice2-phi-real-auth"
ratified_by: chris
promotable: candidate
applies_to_other_brands_potentially: [vitalia, nicolify, comunify, lupulo]
target_core_package: core/luana-core-iam (helper de minteo para tests/verificación)
tags: [clerk, jwt, jwks, godmatrix, verificacion-real, anti-teatro, phi, auth, rbac]
---

# Verificación live de auth con JWT real de Clerk (god-matrix mint pattern)

## Contexto

Slice 2 PHI desentubó el decoder JWT (stub → JWKS real). Los tests integration monkeypatchean `verify_token_payload` → deterministas pero **NO ejercen el JWKS real**. Para cumplir "verificación real ≠ HTTP 200" (anti-teatro) había que ejercer el flujo con un **JWT real de Clerk** contra el dev-app.

## Aprendizaje

Se puede mintear un JWT real de Clerk para un usuario seed (god-matrix) vía **Clerk Backend API**, sin login interactivo:

```bash
# 1. Crear sesión para el user_id (sk_test, instancia dev)
sid=$(curl -s -X POST "https://api.clerk.com/v1/sessions" \
  -H "Authorization: Bearer $CLERK_SECRET_KEY" -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\"}" | jq -r .id)
# 2. Mintear JWT de esa sesión (default template, ~60s TTL)
#    ★ corrección 2026-05-30 (story vitalia-crm-phi-base-tables-migration): el endpoint
#    /v1/sessions/{id}/tokens ahora EXIGE Content-Type: application/json (devuelve
#    {"errors":[{"code":"unsupported_content_type"}]} sin él → jwt=null → todo 401).
jwt=$(curl -s -X POST "https://api.clerk.com/v1/sessions/$sid/tokens" \
  -H "Authorization: Bearer $CLERK_SECRET_KEY" -H "Content-Type: application/json" | jq -r .jwt)
# 3. Ejercer el endpoint PHI con el JWT real + headers reales
curl -s -o /dev/null -w "%{http_code}" "$EP" \
  -H "Authorization: Bearer $jwt" -H "X-Tenant-ID: $TENANT" -H "X-Clinic-ID: $CLINIC"
```

Resultado god-matrix Slice 2: doctor real → **200**, marketing real → **403**, forjado → **401**, stub legacy → **401**. Esto probó que el desentubado funciona end-to-end (el origen era PHI rechazando JWT real → 401).

## Aplicación práctica

- **Cuándo aplica:** verificar live cualquier cambio de auth/RBAC sobre superficies Clerk-protegidas (cualquier brand — todas usan Clerk como identity provider). Reemplaza el "salió 200 = funciona" por ejercicio real + lectura de logs.
- **Cómo aplica:** mint vía Backend API (3 curls) + ejercer el endpoint + leer `docker logs <backend> | grep -iE '401|403|500|traceback|does not exist'`. NUNCA imprimir secret/JWT/PHI en el transcript (solo status codes + logs sanitizados — HIPAA-lite).
- **Cuándo NO aplica:** tests CI deterministas (ahí monkeypatch `verify_token_payload`; el mint real es para la verificación supervisada/god-matrix, requiere egress + CLERK_SECRET_KEY).

## Refuerzo · verificación real ≠ HTTP 200

El monkeypatch verde NO basta: al ejercer el flujo real surgieron 2 gaps que los tests no veían — tablas `vitalia_patients`/`vitalia_leads` faltantes en dev (500) — invisibles bajo mock. El anti-teatro encuentra lo que el mock esconde. Ver `[[verification-real-not-200]]` + `test-design-doctrine.md § Verificación REAL ≠ "HTTP 200"`.

## Referencias

- Story: `vitalia/docs/archive/2026/stories/vitalia-iam-slice2-phi-real-auth/` (07-merge.md + VERIFICATION-godmatrix-live.md)
- Engine JWKS: `core/luana-core-iam/src/luana_core_iam/application/auth.py::verify_token_payload`
- Seed god-matrix: `vitalia/backend/scripts/seed_test_users_link.py`
- Rule: `.claude/rules/test-design-doctrine.md`
