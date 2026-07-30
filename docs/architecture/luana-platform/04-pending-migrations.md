---
id: ADR-luana-platform-004
date: 2026-05-16
status: accepted
owner: /pm-luana
audience: /pm-luana + /pm-nicolify + futuras brand owners
related:
  - docs/architecture/luana-platform/01-core-audit.md
  - docs/architecture/luana-platform/03-nicolify-carve-out-audit.md
  - docs/promotion-protocol/README.md
  - docs/process/learnings.md (entry 2026-05-16 ap_sales_agent diff)
---

> [HISTÓRICO — read-only. Lista de migraciones planificada durante el reorg multibrand; varias ya completadas o supersedidas. No usar como tracker vigente. Conservado por trazabilidad.]

# Pending migrations — código en `/home/chalreme/Documentos/ap_sales_agent/`

> **Snapshot referencial:** `/home/chalreme/Documentos/ap_sales_agent/` es el monolito Nicolify pre-reorg (`luana-platform/` multimarca cementada 2026-05-15). Está **fuera del repo `luana-platform/`** y se usa como **museo read-only** hasta que todo lo útil esté migrado.
>
> **Regla:** prohibido editar `ap_sales_agent/`. Cualquier rescue de código pasa por este documento (decisión + destino + commit).

## Contexto

Audit cruzado `ap_sales_agent/` vs `luana-platform/` (2026-05-16) reveló 3 items pendientes:

| Item | Estado original | Estado luana-platform | Decisión 2026-05-16 |
|---|---|---|---|
| `backend/tests/migrations/` (6 tests) | 6 archivos de tests sobre migrations Alembic 116-125 + T-3 | NO existen | **Skip rescue — obsoletos por design (ver § 1)** |
| `shopify_app/` (sub-app entera) | 348K código propio (Shopify integration) | NO existe | **Defer hasta primer cliente (ver § 2)** |
| `client_simulator/` (sub-app entera) | 280K (LangGraph customer simulator + SQLite) | NO existe pre-2026-05-16 | **Rescatado a `apps/client-simulator/` (ver § 3)** |

## § 1. 6 migration tests — obsoletos por design

### Tests originales

```
ap_sales_agent/backend/tests/migrations/
├── test_116_litellm_db_marker.py            # separate DB visionarias_litellm_db (CREATE DATABASE)
├── test_117_llm_role_binding.py             # tabla llm_role_binding + llm_config_audit + COALESCE
├── test_118_seed.py                          # 6 ModelRoles INSERT NOT EXISTS
├── test_119_llm_eval_gate.py                 # tabla llm_eval_gate_runs + threshold + 6 seed inserts
├── test_extend_eval_simulator_observability.py  # 3 eval_simulator tables + 7 indexes
└── test_t3_pricing_snapshot_repair.py       # backup table + 3 UPDATEs (deepseek/kimi/dashscope)
```

### Por qué son obsoletos

Story 10 T-10 (2026-05-14) **consolidó las 131 migrations originales** en `001_initial_snapshot.py` (single idempotent snapshot generated from `pg_dump --schema-only`). Las migrations individuales 116-125 + 122 (T-3) ya **no existen como archivos sueltos** — están dentro del snapshot.

Los 6 tests originales hacen `importlib.util.spec_from_file_location("alembic/versions/116_*.py")` — su path target NO existe post-collapse. **No "se perdieron" — se volvieron obsoletos por design.**

### Análisis de rescue parcial (considerado, descartado)

| Test original | Naturaleza | Re-write contra snapshot? |
|---|---|---|
| test_116 (CREATE DATABASE) | deploy-time concern | ❌ no aparece en schema snapshot |
| test_117 (DDL llm_role_binding) | schema | ✅ posible como schema regression test |
| test_118 (seed 6 roles) | seed data (INSERTs) | ❌ snapshot solo es DDL, sin seeds |
| test_119 (DDL + 6 thresholds) | mixto schema/seeds | ⚠️ parcial (schema sí, seeds no) |
| test_125 (eval_simulator schema) | schema | ✅ posible como schema regression test |
| test_t3 (backup + UPDATEs) | mixto schema/data | ⚠️ parcial (backup table sí, UPDATEs no) |

Decisión Chris 2026-05-16: **skip rescue completo** — re-escribir contra snapshot agrega trabajo (~30-50 min) para tests que perdieron mucha de su semántica original (seeds + UPDATE statements quedaron afuera de snapshot). El valor histórico ya cumplió función pre-collapse.

### Acción futura (cuando alguien quiera schema regression coverage)

Si en algún momento querés protección contra "alguien rompe schema crítico":
- Re-escribir solo 117 + 125 + t3-backup-parts como `nicolify/backend/tests/migrations/test_snapshot_schema_regression.py` (single file consolidado)
- Apunta a `001_initial_snapshot.py`, verifica que las tablas + índices + CHECK constraints críticos NO desaparecieron
- Trabajo estimado: ~45 min

**Mientras tanto:** snapshot mismo tiene comentarios cementando expectations + `make verify-migration` cubre idempotency end-to-end con DB real.

## § 2. shopify_app — defer hasta primer cliente

### Inventario original

```
ap_sales_agent/shopify_app/                     (348K código propio, sin contar node_modules)
├── package.json                                 # Node.js + Shopify CLI
├── shopify.app.toml + shopify.app.prod.toml    # Shopify app config dev/prod
├── generate-config.sh                           # script de generación
└── .shopify/{deploy-bundle,dev-bundle}/         # Shopify deployment bundles
```

### Por qué defer

Chris (2026-05-16): "shopify_app no nos va a servir para todos, solo para algunos". Es una integración channel adapter que **solo aplica a brands con ecommerce/D2C orientation**. Candidatos potenciales:

- **Retailly** (E-commerce / D2C — primer candidato natural, Shopify es proveedor mainstream)
- **Nicolify** (si alguna agencia B2B tiene cliente con Shopify storefront)
- Posiblemente Comunify (si alguien vende cursos via Shopify storefront)

### Decisión

**No migrar ahora.** Permanece en `ap_sales_agent/shopify_app/` como referencia. Cuando aparezca el primer cliente real que lo necesite:

| Opción A | Opción B |
|---|---|
| `{brand}/integrations/shopify_app/` | `core/luana-core-connections/adapters/shopify/` (engine + EP-8 channel adapter) |
| Single-brand consumer | Cuando ≥2 brands lo piden (anti-duplication lift) |

Decisión final = en su momento, basado en cuántas brands lo necesitan.

### Acción mientras tanto

`ap_sales_agent/shopify_app/` preservado como museo read-only. Cuando el cliente aparezca, abrir promotion proposal en `docs/promotion-protocol/proposals/`.

## § 3. client_simulator — rescatado 2026-05-16

### Decisión

**Migrado a `apps/client-simulator/`** como engine compartido + scenarios per-brand. Pattern análogo a `apps/test-brand/`.

### Estructura final

```
apps/client-simulator/                              ← engine (cross-brand)
  src/{simulator, infrastructure, domain}/         — LangGraph + customer node + agent bridge
  .env.example                                      — BACKEND_URL parametrizable per brand
  pyproject.toml                                    — luana-client-simulator v0.2.0
  README.md                                         — uso + filosofía + estado integración
  .env                                              — borrado (tenía secrets, .gitignored)

{brand}/backend/tests/agentic_evals/simulator/scenarios/
  README.md                                         — stub per-brand explicando dónde poner scenarios
  (stubs creados para vitalia, comunify, nicolify; lupulo placeholder skip)
```

### Estado integración pendiente

Engine está **preservado, NO integrado al stack multimarca aún**. Faltan:

1. Refactor `src/simulator/agent_bridge.py` para usar brand resolver
2. CLI parametrizable por `--brand {slug}` + scenario loader
3. Conectar a observability eval bucket (`eval_simulator_*` tablas ya están en snapshot)
4. Docs de cómo crear scenarios per-brand

**Trabajo estimado:** M (~3-5 días) — story futura cuando se quiera empezar a usar simulator para QA agentic cross-brand.

## Tabla resumen final

| Pending | Decisión 2026-05-16 | Acción futura |
|---|---|---|
| 6 migration tests | Skip rescue (obsoletos por design post Story 10 T-10 snapshot collapse) | Opcional: re-write como `test_snapshot_schema_regression.py` (~45 min) si querés guard regression DDL |
| shopify_app | Defer hasta primer cliente lo necesite | Migrar a `{brand}/integrations/` o `core/luana-core-connections/adapters/shopify/` según N=1 o N≥2 brands |
| client_simulator | ✅ rescatado a `apps/client-simulator/` + stubs per-brand | Story M futura: integrar al stack multimarca (refactor agent_bridge + CLI + scenario loader) |

## Referencias

- Original source: `/home/chalreme/Documentos/ap_sales_agent/` (4.9GB, read-only museum)
- Audit diff completo: ver `docs/process/learnings.md` entry 2026-05-16 ap_sales_agent diff
- Story 10 T-10 snapshot consolidation: `nicolify/backend/alembic/versions/001_initial_snapshot.py` (131 migrations → 1 file)
- Nicolify carve-out plan: `docs/architecture/luana-platform/03-nicolify-carve-out-audit.md`
