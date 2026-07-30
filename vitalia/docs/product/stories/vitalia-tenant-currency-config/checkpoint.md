---
story_id: vitalia-tenant-currency-config
type: ui-story
agent_owner: config
map_zone: plataforma
map_box: configuracion
map_area: cuenta
module: iam
capability: configuracion.cuenta   # currency = preferencias regionales (timezone/moneda) · área real SYSTEM-MAP (era 'config.currency' inválido)
state: idea
architecture_pattern: ADR-vitalia-004
last_modified: 2026-06-17
ratified_by_chris: false
parallel_safe: true
priority: high
estimated_dev_days: 3-4
dependencies:
  hard:
    - vitalia-fase1-routing-shell
  soft: []
blocks_hard: []
blocks_soft: []
engine_coordination:
  # El campo primary (default_currency) YA existe en engine iam. El secondary
  # currency + validación ISO 4217 en core/luana-core-iam es un LIFT /pm-luana
  # (engine change cross-brand). Esta story vitalia owns el FE + el wiring +
  # test-data PEN; la extensión del engine se escala a /pm-luana en refinement.
  - "core/luana-core-iam: agregar secondary_currency a Tenant settings + validación ISO 4217 (lift /pm-luana)"
reuse_map_summary: >-
  EXTEND engine iam (core/luana-core-iam: tenant.default_currency YA existe + settings
  GET/PATCH) — primary currency ya modelada. NET-NEW: secondary_currency (lift /pm-luana),
  selector ISO 4217 (UI + lista de códigos), UI settings en Plataforma/Configuración,
  wire useTenantLocale al source canónico del tenant (matar fallback hardcoded ARS),
  test tenants → PEN. CONSUME core/luana-core-platform locale.py + currency.py
  (FALLBACK_CURRENCY). CERO mirror.
spawned_at: 2026-06-17
origin: "Chris detectó moneda ARS hardcodeada verificando vitalia-fase2-lisa-servicios (G round 2, 2026-06-17). El ARS NO era bug de lisa-servicios sino del fallback pre-existente useTenantLocale.ts + seed Sanaré default_currency=ARS sin currency en publicMetadata."
release: F4
cap_target: configuracion.cuenta   # SYSTEM-MAP area (moneda vive en config Cuenta) · era 'config.currency' (box inválido + área no registrada · bloqueaba el gate SYSTEM-MAP en main)
cap_change_type: null
parent_story: null
next_action: >-
  /pm-vitalia intake-handshake hecho (zona Plataforma/Configuración · extends iam settings).
  Próximo: refinar con /po-ux (UI selector ISO 4217 primary+secondary) — coordinar el lift
  engine iam (secondary_currency) con /pm-luana. Quick-win previo posible: flip test tenants
  a PEN (seed default_currency + publicMetadata.currency + --clerk-sync) vía /dev-team.
---

# vitalia-tenant-currency-config — checkpoint

## Goal

El tenant/clínica configura su **moneda primaria + secundaria** (ISO 4217), y esa
moneda **proviene del tenant** (source canónico), nunca de un fallback hardcodeado.
Toda superficie que muestra precios (offers, planes de pago, escalera, dashboards)
consume la moneda del tenant.

## Por qué (origen)

Chris vio precios en **ARS** verificando `lisa-servicios` (G round 2, 2026-06-17).
El ARS NO era bug de lisa-servicios (consume `locale.currency` correctamente). Sale de:

1. **FE fallback hardcoded:** `vitalia/frontend/src/hooks/useTenantLocale.ts` →
   `VITALIA_DEFAULT_LOCALE.currency = "ARS"` (story `vitalia-fe-tenant-resolution`
   2026-06-01). El propio hook tiene un TODO: "wire actual tenant locale endpoint…
   follow-up story" — **esta es esa story**.
2. **Seed sin currency en metadata:** `vitalia/backend/scripts/seed_test_users_link.py:93`
   pone Sanaré (demo tenant `e69a691d`) `default_currency: "ARS"`, y el `--clerk-sync`
   pushea `publicMetadata.{role,tenant_id,clinicId}` pero **NO `currency`** → el FE
   cae al fallback ARS.
3. **Call-sites `?? "USD"` (G2-F9 · auditoría lisa-servicios 2026-06-19):** `ServiceCard.tsx:67`
   + `RungColumn.tsx:54` aún usan `currency ?? "USD"` mientras `ResumenView.tsx:390` ya aplica
   el canon (inconsistencia intra-story). El auditor-frontend de lisa-servicios los nombró como
   WARN Cat 8 y los routeó acá. Esta story DEBE matar esos 2 call-sites (Server Components, el
   hook no es alcanzable → resolver currency del tenant en el server).

## Prior art scan (anti-duplication-refining · 2026-06-17 · intake)

| Fuente | Resultado | Decisión |
|---|---|---|
| `core/luana-core-iam` (`domain/tenant.py`, `infrastructure/models/tenant_model.py`, `api/settings.py`) | `tenant.default_currency` (String, server_default=FALLBACK_CURRENCY) + settings GET/PATCH ya exponen `default_currency` | **EXTEND vía /pm-luana lift** — primary currency YA existe; agregar `secondary_currency` + validación ISO 4217 |
| `core/luana-core-platform/domain/{locale,currency}.py` | `TenantLocale` VO (`currency: str`) + `FALLBACK_CURRENCY="USD"` + `TenantLocale.default()` | CONSUMIR — la conversión/display ya está modelada en el engine |
| `vitalia/frontend/src/hooks/useTenantLocale.ts` | lee `user.publicMetadata.currency` + fallback hardcoded ARS | **MODIFICAR** — wire al source canónico del tenant + matar fallback AR-specific |
| `comunify/` live | (revisar en refining — currency display) | posible patrón paralelo / lift candidate |

## Scope (borrador — refinar con /po-ux)

1. **Engine (lift /pm-luana):** `core/luana-core-iam` Tenant settings → agregar
   `secondary_currency: str | None` + validación ISO 4217 (primary + secondary).
   Settings API GET/PATCH expone ambos.
2. **FE selector ISO 4217:** UI en Plataforma → Configuración → Cuenta: selector de
   moneda primaria + secundaria (lista ISO 4217). Spanish neutro.
3. **FE wiring:** `useTenantLocale` (o hook nuevo) lee la moneda del **source canónico
   del tenant** (settings endpoint), NO del fallback hardcoded. Matar/neutralizar
   `VITALIA_DEFAULT_LOCALE.currency = "ARS"` (fallback debe ser neutro, p.ej. del
   engine `FALLBACK_CURRENCY`, o resolverse server-side).
4. **Test data:** test tenants (Sanaré `e69a691d` + fixtures) → **PEN**. Seed
   `default_currency` + `--clerk-sync` pushea `currency` a `publicMetadata`.
5. **Limpieza de fallbacks `?? "USD"`** display-side (`RungColumn.tsx:54`,
   `ServiceCard.tsx:67`) — auditar contra master-data rule (NEVER `?? "USD"`).

## Anti-objetivos

- NO conversión de tasas FX en vivo (solo selección de moneda · MVP).
- NO multi-moneda por offer individual (la moneda es del tenant).
- NO tocar la lógica de pricing/cobros (solo la moneda de display + su source).

## Referencias

- `.claude/rules/master-data.md` + `.claude/rules/currency-handling.md` — currency del data source, NUNCA hardcoded
- `core/luana-core-iam/src/luana_core_iam/api/settings.py` — settings GET/PATCH (default_currency)
- `core/luana-core-platform/src/luana_core_platform/domain/currency.py` — FALLBACK_CURRENCY
- `vitalia/frontend/src/hooks/useTenantLocale.ts` — el fallback ARS a matar (tiene el TODO de esta story)
- Origen: `vitalia/docs/product/stories/vitalia-fase2-lisa-servicios/checkpoint.md::upstream_finding_currency`
