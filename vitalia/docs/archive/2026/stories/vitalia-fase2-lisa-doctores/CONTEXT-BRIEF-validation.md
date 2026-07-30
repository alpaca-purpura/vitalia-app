# CONTEXT-BRIEF validation — vitalia-fase2-lisa-doctores DELTA v3 (2026-06-11)

> **Modo de ejecución:** protocolo `context-validator` ejecutado IN-PROCESS por el mismo runtime Haiku (el entorno de esta invocación NO expone Agent tool — spawn imposible, no por omisión sino por toolset: Read/Bash/Write/Edit/WebFetch únicamente). Independencia reducida → el brief se sella `partial`, no `clean`. Probes adversariales con keywords DISTINTOS a los del builder, abajo.

## Probes adversariales (keywords ≠ scan original)

| # | Probe (keyword nuevo) | Resultado | Veredicto vs brief |
|---|---|---|---|
| 1 | `searchFn / EntitySearchFn / @tanstack/react-virtual` en EntityPicker.tsx | Confirmado: query-lib agnostic vía `searchFn` prop (L24, L89), cursor `nextCursor` (L73), windowed via `useVirtualizer` (L40) | ✅ brief §7 correcto |
| 2 | `LEAF_DEFS` en StaffWorkspaceShell.tsx | Existe L45-48 con 3 hojas {perfil, horarios, servicios} — leaf segments ESTÁTICOS (comment L86) | ✅ brief §4; agregar "pagina" ahí es correcto |
| 3 | `Query(default=...)` params en doctors_router.py | `q` L168, `active` L170, `page` L171, `page_size` L172 (default 24, le=100) | ✅ D3-A cero cambio BE confirmado |
| 4 | `presigned / download / get_url` en assets proxy + ports | **HALLAZGO:** el proxy SOLO tiene `POST /upload` (L119). D-3 documentado en el propio archivo: "presigned upload does NOT exist in luana-core-assets" (L8, L139). NO existe mecanismo de download/presigned-GET en el proxy ni en ports | ⚠️ MEDIUM — ver finding F-1 |
| 5 | `PhiRepositoryBase` + audit en clinics | `_shared/repositories/phi_repository.py` existe; `AuditLogRepository` importado en doctors_router L31; 6 repos lo heredan | ✅ brief §5/§9 |
| 6 | `slugify` BE + `generateMetadata` FE | slugify: **0 hits** en `vitalia/backend/src` → util NUEVO para backfill 041. generateMetadata: prior art REAL en `app/public/[clinic-slug]/{page,booking/page}.tsx` | ⚠️ LOW ×2 — findings F-2, F-3 |
| 7 | `Intl / es-419` en AvailabilityCalendar | Patrón existente confirmado (L36-67, "NEVER toLocaleDateString", locale explícito es-419) | ✅ brief §2 master-data claim |

## Re-verificación de 3 claims aleatorios del brief §7

1. "`_VALID_KINDS` L59 = {avatar, credential_doc}" → re-grep ✅ exacto.
2. "`entityIdentitySlot` 0 hits (greenfield)" → re-grep ✅ 0 hits en core + vitalia.
3. "proxy.ts `isPublicRoute` sin `/d/`" → re-read L33-50 ✅ (`/public(.*)` sí está; `/d/` no).

## Claim §15 (web fetch)

dateutil rrule docs (fetched este run, cache 15min): `count` = ocurrencias totales cross-weekday (ejemplo doc Tue+Thu count=10 → 10 fechas) + `until` inclusivo por igualdad. ✅ consistente con lo embebido en §15.

## Findings

- **F-1 (MEDIUM · gap del arch, no del brief):** `GET /{doctor_id}/bio-files/{file_id}/download` asume "resolves presigned/proxy URL via AssetsService" (03-arch-delta § 3.1) pero NO existe NINGÚN path de lectura/presigned hoy (proxy = upload-only; D-3 niega presigned en el engine para upload). Builder T-BE-bio-docs debe inspeccionar la superficie real de `luana_core_assets.application.assets_service.AssetsService` (consume read-only, NUNCA editar engine) y probablemente construir: GET proxy stream (boto3 `get_object`) o presigned-GET brand-local (boto3 `generate_presigned_url`). Cómo se "descarga" el avatar hoy NO sienta precedente (avatarKey solo se PATCHea; no se encontró GET).
- **F-2 (LOW):** `slugify` para `public_slug` backfill (mig 041) no existe en BE — implementar util chico (determinístico, colisión → sufijo numérico, per arch).
- **F-3 (LOW · prior art positivo):** `app/public/[clinic-slug]/{page,booking}` ya implementan páginas públicas sin auth (cubiertas por `/public(.*)` en isPublicRoute) CON `generateMetadata` — referencia directa para T-FE-pagina-publica (OG tags + Server Component fetch). La ruta nueva `/d/**` es deliberadamente otra (ratificada en spec); el patrón se copia, la ruta no.
- **F-4 (LOW):** brief §16 estimaciones de tool-calls aproximadas (cosmético).

## Veredicto

Sin discrepancias HIGH: ningún sistema existente omitido, ningún claim factual del brief refutado. F-1 incorporado al brief (§11 + §14). **Flag final: `partial`** (modo in-process + F-1 MEDIUM).
