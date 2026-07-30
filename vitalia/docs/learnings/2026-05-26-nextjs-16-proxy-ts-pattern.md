<!-- voseo-allowed: internal learning documentation, not user-facing -->
---
brand: vitalia
date: 2026-05-26
slug: nextjs-16-proxy-ts-pattern
promotable: candidate
applies_to_other_brands_potentially: [nicolify, comunify, lupulo]
target_core_package: null  # FE pattern, no engine package específico — candidate para core/luana-core-frontend-shared/ futuro
origin_story: vitalia-fase1-routing-shell
---

# Next.js 16 proxy.ts + Clerk middleware pattern

**Qué aprendimos:** Next.js 16 deprecó `middleware.ts` en favor de `proxy.ts`. Función exported debe llamarse `proxy` (no `middleware`). Runtime es **Node.js only** (no edge configurable). Config flag renombrada `skipMiddlewareUrlNormalize → skipProxyUrlNormalize`. Clerk 6.x sigue exponiendo `clerkMiddleware()` helper (nombre del helper NO cambió, solo el file). Matcher canónico Clerk 2026 obligatorio incluye `/__clerk/(.*)` para que Clerk auth proxy interno funcione.

**Origen:** F1-S9 vitalia-fase1-routing-shell (2026-05-26). Story upgrade vitalia frontend a Next.js 16.2.3 + Clerk 6.36.8 con `proxy.ts` + tenant validation server-side en layout.

**Why:** Sin este pattern, vitalia/frontend en Next.js 16 mostraría deprecation warnings + posible auth break en producción. El equivalente correcto es `proxy.ts` con:
- `auth.protect()` (no `auth().protect()` — API moderna Clerk 2026)
- `createRouteMatcher(['/sign-in(.*)', '/sign-up(.*)', '/marketing(.*)', '/public/(.*)', '/__clerk/(.*)'])` para rutas públicas
- Matcher config: `'/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)'`

**How to apply (cuándo aplica cross-brand):**

Trigger condición: brand upgrade a Next.js 16.x.

Pasos canónicos:

1. `npx @next/codemod@canary middleware-to-proxy .` (codemod oficial Next.js renombra archivo + función)
2. Verificar `proxy.ts` queda en `src/` o root (mismo nivel que `app/`)
3. Actualizar matcher para incluir `/__clerk/(.*)` (Clerk 2026 obligatorio)
4. `createRouteMatcher` para definir rutas públicas (sign-in, sign-up, marketing, public)
5. `auth.protect()` en branch default

**Tenant validation pattern (DEFENSE-IN-DEPTH 3 capas — vitalia HIPAA-lite):**

1. `proxy.ts` — solo auth check (sesión Clerk válida), NO tenant_id
2. Layout server component — fetch user tenants via BE (`GET /api/v1/iam/users/me/tenants`) + valida `params.tenantId` ∈ lista del usuario
3. BE API per request — re-valida `tenant_id` (defense-in-depth final)

Next.js docs explícitamente recomiendan: "Always verify authentication and authorization inside each Server Function rather than relying on Proxy alone."

**Anti-pattern detectado y evitado:**

- ❌ NO duplicar endpoint `/me/tenants` per brand. Vive en `core/luana-core-iam/src/luana_core_iam/api/routers/auth_router.py:23`. Brand backend lo MONTA via:
  ```python
  from luana_core_iam.api.routers import auth_router as iam_users
  app.include_router(iam_users.router, prefix="/api/v1/iam/users", tags=["IAM - Users"])
  ```
  Pattern referencia: `nicolify/backend/src/main.py:543` (paridad verbatim).

**HIPAA-lite audit log (vitalia overlay):**

Cross-tenant attempt + no-tenants-assigned events → log via `console.warn("[audit]", {userId, attemptedTenant, timestamp})`. PII-safe: SOLO `userId + attemptedTenant_id + timestamp + ip` (NO patient names, NO emails). BE audit endpoint diferido Fase 2 (transport actual: console.warn, F2 escribirá a tabla `audit_log` con retention 10y).

**Sources canónicos (current 2026-05):**

- https://nextjs.org/docs/app/api-reference/file-conventions/proxy
- https://clerk.com/docs/reference/nextjs/clerk-middleware

**Aplicación cross-brand sugerida:**

| Brand | Estado Next.js | Aplicar pattern |
|---|---|---|
| Vitalia | Next.js 16.2.3 ✅ | YA aplicado (F1-S9) |
| Nicolify | Next.js 15.x | Cuando upgrade → seguir este pattern |
| Comunify | Next.js 15.x | idem |
| Lupulo Labs | placeholder | desde día 1 |

**Promotion candidate to core:**

`/pm-luana` evaluar lift cuando ≥2 brands aplican. Target: `core/luana-core-frontend-shared/proxy.ts` o documentación canónica en `docs/core-modules/frontend-patterns.md`. Por ahora vitalia-only.
