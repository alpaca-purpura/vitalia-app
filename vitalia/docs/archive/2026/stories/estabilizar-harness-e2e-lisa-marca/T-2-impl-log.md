# T-2 impl-log — FE-prod: actor de audit real (sub-bug #2)

> Owner ejecución: builder-frontend (Sonnet). Orchestrator: /dev-team (Opus).
> Surface: `vitalia/frontend/src/features/lisa/api/marca-voice-api.ts` + su test. Cero BE, cero core.
> Depende de: T-3 (pushed, `5ef8cdd4`) — el BE ya resuelve `clerk userId → users.id`.

## Scope (acotado por el orchestrator tras inspección live)

**EN SCOPE (T-2):**
- `marca-voice-api.ts::updatePersonality` línea 113: `"X-User-ID": opts.tenantId` → mandar el **Clerk userId real** (`opts.userId`). El hook `usePersonalityAutosave.ts:50,61` YA pasa `userId` (de `useAuth()`) — solo la api-fn lo ignoraba. **NO** fallback a `tenantId` (eso es el bug). Borrar el comentario que racionaliza el placeholder.
- Test HONESTO a nivel **api-function** (mockear `fetchClient`, asertar el header `X-User-ID` real === Clerk userId, ≠ tenantId). **NO** mockear `updatePersonality` (eso es el false-green que esta misma story combate — RN-1).

**FUERA DE SCOPE (documentado follow-up, NO tocar en T-2):**
- `postVoiceWarningOverride` (marca-voice-api.ts:139): NO manda `X-User-ID` (depende de fetchClient que solo inyecta X-Tenant-ID). Si el endpoint BE audita y requiere actor, es un gap **pre-existente y separado** (no es el sub-bug #2 declarado). Flag para /pm-vitalia.
- `identity` / `visuals` / `contact` mutations: viven en OTROS api files (no `marca-voice-api.ts`), fuera del file-scope de T-2. Mismo bug latente (mandan `tenantId` como actor) pero el ticket scopea solo `marca-voice-api.ts::updatePersonality`. **Follow-up bugfix** para /pm-vitalia (el BE T-3 ya soporta el actor real para esos endpoints; solo falta el FE).

Razón del corte: D3 scope discipline — el ticket declara `marca-voice-api.ts::updatePersonality`. Expandir a otros api files = scope creep. SC-6 valida personality. Lo demás se documenta honesto, no se shippea a medias sin registrar.

## Plan TDD (RED→GREEN)

1. RED: test api-function `updatePersonality` mockeando `fetchClient` → assert `X-User-ID` header === `opts.userId` (ej. `user_2abc`), ≠ `opts.tenantId`. Contra el código actual (manda tenantId) → RED.
2. GREEN: cambiar línea 113 a `opts.userId` (con guard si null — no mutación anónima).
3. Verde: vitest + tsc + eslint + arch-fitness FE (`test-no-clerk-organizations.test.ts` sigue verde — usamos `useAuth().userId`, NO `orgId`).

## Iteration log

### iter-1 — 2026-06-03 — builder-frontend (Sonnet) — GREEN

**RED-first (TDD):**
- NEW `src/features/lisa/api/__tests__/marca-voice-api.test.ts` (mockea `fetchClient`, ejerce `updatePersonality` real). Contra el código actual (manda `tenantId`, sin guard) → **4 fallos RED** confirmados: `X-User-ID === userId`, `X-User-ID !== tenantId`, guard `userId null` rejects, guard `userId undefined` rejects. Los 3 que pasaron desde RED (role/method) son ortogonales, no tocados.

**GREEN (fix prod):**
- `marca-voice-api.ts::updatePersonality`: `"X-User-ID": opts.tenantId` → `"X-User-ID": opts.userId`. Guard `if (!opts.userId) throw` (no mutación anónima, **sin** fallback a `tenantId` que reintroduciría el bug). Comentario placeholder (líneas ~105-111) reescrito: ahora documenta que el BE resuelve el actor desde `clerk_sub` (T-3 #2b) y el FE forwardea el Clerk userId real.
- `usePersonalityAutosave.test.ts` (coverage_update): agregado `userId` al mock de `@clerk/nextjs` (antes lo omitía → `undefined`) + 2 tests nuevos asertando que el hook pasa `opts.userId === Clerk userId` y `!== tenantId` a `updatePersonality`. El assert del HEADER vive en el api-fn test (es donde se construye el header); aquí se asserta el ORIGEN del actor (el hook).

**G5 gates (literal, ver T-2-result.md):**
- `tsc --noEmit` → EXIT 0 (0 errores).
- `eslint src/features/lisa/api/` + hook test → EXIT 0 (0 warnings).
- `vitest run` api + hook → 74/74 GREEN (incl 7 nuevos api-fn + 2 nuevos hook).
- `vitest run src/__tests__/architecture/` → 171/171 GREEN (25 files; `test-no-clerk-organizations` 16/16 — seguimos usando `useAuth().userId`, NO `orgId`).

**Notas de entorno:** worktree aislado sin `node_modules` propio → gates corridos con symlink temporal al `node_modules` del shared checkout `luana-vitalia` (vitest pinned v2.1.9), symlink removido pre-commit (no se stagea).

**Fuera de scope confirmado (no tocado):** `postVoiceWarningOverride`, `fetchClient.ts`, api files `identity/visuals/contact`, BE, e2e. Follow-up para /pm-vitalia documentado arriba (§ Fuera de scope) + reiterado en T-2-result.md.
