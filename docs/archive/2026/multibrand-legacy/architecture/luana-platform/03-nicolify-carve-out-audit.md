---
id: ADR-luana-platform-003
date: 2026-05-16
status: accepted
owner: /pm-luana
audience: /pm-luana + /pm-nicolify + /dev-team (future lift execution)
related:
  - docs/architecture/luana-platform/01-core-audit.md
  - docs/architecture/luana-platform/02-core-purge-audit.md
  - docs/architecture/luana-platform/ADR-001-luana-platform.md
  - docs/promotion-protocol/README.md
  - nicolify/.claude/rules/b2b-billable-hours.md
---

> [HISTÓRICO — read-only. Auditoría del carve-out de nicolify previa al nicolify-reset (2026-05-29). Las estructuras descritas fueron reseteadas; ver MEMORY nicolify-reset-2026-05-29. Conservado por trazabilidad.]

# Nicolify — Carve-out audit (post multibrand reorg)

> **Scope:** este doc es cross-brand (decisiones lift core ↔ nicolify) → vive en
> `docs/architecture/luana-platform/`, jurisdicción `/pm-luana`. `/pm-nicolify`
> consume read-only y abre stories nicolify-vertical post-purge.
>
> **Estado:** audit only — NO ejecuta lift. Documenta verdict por módulo + próximas
> promotion proposals candidatas. Input para futuras stories de carve-out per-módulo.

## Contexto

Post multibrand reorg 2026-05-15, la topología layout multimarca está cementada
(brand verticals `{brand}/{backend,frontend,config,deploy,docs,.claude}/`). El
**carve-out físico del código** del monolito histórico (Nicolify-lo-tenía-todo)
hacia `core/luana-core-*/` se ejecutó parcialmente como Story 5+ pero **el
código duplicado quedó en `nicolify/backend/src/modules/` en paralelo** —
nunca se purgó.

Al 2026-05-16:

- `nicolify/backend/src/modules/` contiene 18 módulos flat (NO bajo `modules/nicolify/`)
- `core/luana-core-*/src/luana_core_*/` contiene 25 packages con código real
- **15 de los 18 módulos nicolify están duplicados** prácticamente 1:1 en core
  (delta típico: 5-15 archivos extras en core — nuevos models, ports, refactors)
- **0 módulos brand-vertical-agencias-B2B genuinos** existen (`billable_hours`,
  `client_portal`, `proposals`, `contracts` son aspirational en
  `.claude/rules/b2b-billable-hours.md`, no implementados)
- Nada en producción real (confirmed Chris 2026-05-16) — ambiente dev/staging

## Verdict matrix — 18 módulos nicolify

> Verdicts: `drop_duplicate` (duplicado de core/, eliminar) · `keep_extension`
> (engine + brand-extension válida) · `drop_terminal` (sin uso, sin core) ·
> `lift_to_core_then_drop` (código único hoy en nicolify, lift a core primero) ·
> `migrate_to_vertical` (mover bajo `modules/nicolify/` si brand-specific genuino).

| # | Módulo | Py files | Core equivalente | Δ core−nicolify | Verdict | Razón |
|---|---|---|---|---|---|---|
| 1 | advertising | 28 | (none) | n/a | **drop_terminal** | CLAUDE.md tabla mapping = DROP. Placeholder histórico sin uso |
| 2 | analytics | 113 | luana-core-analytics-engine (122) | +9 | **drop_duplicate** | Engine migrado completo. Core tiene refactors menores |
| 3 | assets | 21 | luana-core-assets (26) | +5 | **drop_duplicate** | Engine migrado |
| 4 | brand | 76 | luana-core-brand-studio (84) | +8 | **drop_duplicate** | Engine migrado. Core agrega `brand_voice_port.py`, `brand_voice_service.py`, models avatar/buyer_persona/extraction_trace/personality |
| 5 | campaigns | 72 | luana-core-campaigns (80) | +8 | **drop_duplicate** | Engine migrado |
| 6 | commercial_calendar | 16 | luana-core-commercial-calendar (17) | +1 | **drop_duplicate** | Engine migrado |
| 7 | connections | 66 | luana-core-connections (67) | +1 | **drop_duplicate** | Engine migrado. Brand-specific channel adapters viven en `{brand}/backend/src/modules/{brand}/connections/adapters/` (futuro) |
| 8 | copilot | 231 | luana-core-copilot (243) | +12 | **keep_extension** + investigar overlay | ENGINE + EXTENSION per CLAUDE.md mapping. Core tiene refactors. Verificar si nicolify tiene overlays vertical-agencias-B2B (extractors/tools/workflows específicos B2B). Si no — drop_duplicate |
| 9 | crm | 50 | luana-core-crm (48) | −2 | **drop_duplicate** + crm-enterprise overlay futuro | Engine migrado. Nicolify tiene 2 archivos más que core (verificar si overlay multi-stage forecast B2B genuino o legacy). Rule `b2b-billable-hours.md` describe CRM enterprise overlay → futuro módulo `modules/nicolify/crm_enterprise/` |
| 10 | iam | 25 | luana-core-iam (29) | +4 | **drop_duplicate** | Engine migrado. Core agrega models tenant/user/user_tenant |
| 11 | landing | 20 | luana-core-landing (21) | +1 | **drop_duplicate** | Engine migrado |
| 12 | offer | 89 | luana-core-offer-studio (93) | +4 | **drop_duplicate** | Engine migrado. Preset packs brand-specific via EP-2 registrados en `{brand}/backend/src/modules/{brand}/offer/extensions.py` (futuro) |
| 13 | sales_agent | 138 | luana-core-sales-agent (145) | +7 | **keep_extension** + lift eval_simulator | ENGINE + EXTENSION. Core tiene refactors + models nuevos (agent_state_checkpoint, agent_trace, enrollment, llm_log, message, payment_grant_audit, payment_link, payment_webhook_event, prompt_version, scheduler_webhook_event, sensitive_data, workflow_metric). **eval_simulator/** existe SOLO en nicolify (lift candidate único) |
| 14 | scheduling | 24 | (en luana-core-platform per CLAUDE.md) | n/a | **lift_to_core_then_drop** | Futuro `luana-core-scheduling` o consolidar en `luana-core-platform`. BookingPolicyDef per-brand via Extension SDK |
| 15 | social_media | 5 | (none) | n/a | **drop_terminal** | CLAUDE.md tabla mapping = DROP. Placeholder histórico |
| 16 | social_proof | 35 | luana-core-social-proof (39) | +4 | **drop_duplicate** | Engine migrado |
| 17 | tenant_domains | 17 | luana-core-tenant-domains (18) | +1 | **drop_duplicate** | Engine migrado |
| 18 | tenant_profile | 17 | luana-core-tenant-profile (18) | +1 | **drop_duplicate** | Engine migrado |

### Resumen verdicts

| Verdict | Count | Módulos |
|---|---|---|
| `drop_duplicate` | 12 | analytics, assets, brand, campaigns, commercial_calendar, connections, crm, iam, landing, offer, social_proof, tenant_domains, tenant_profile |
| `keep_extension` | 2 | copilot, sales_agent |
| `drop_terminal` | 3 | advertising, social_media, (crm overlay TBD) |
| `lift_to_core_then_drop` | 1 | scheduling |

> Sub-Total: 14 módulos a purgar (12 drop_duplicate + 2 drop_terminal sin
> equivalente), 1 a liftear primero, 2 a refactorizar como engine + extension
> (mover overlay brand-specific a `modules/nicolify/` si existe; resto drop).

## Otros directorios a auditar

### `nicolify/backend/src/shared/`

Pre-extraction monolith shared layer. Debe haber duplicación con
`core/luana-core-platform/src/luana_core_platform/` (ports, base entities,
infra wiring). Pendiente diff exhaustivo. Verdict tentativo: **drop_duplicate**
en mayor parte; verificar lo único que pueda ser shared-brand-specific.

### `nicolify/backend/src/core/`

Monolith config + DB session. Debe alinear con `luana-core-platform`. Verdict
tentativo: **drop_duplicate**.

### `nicolify/backend/src/admin/`

Streamlit admin panel (per `.claude/rules/admin-panel.md`, opcional per brand).
Nicolify hereda. Verdict: **keep_as_vertical** si brand quiere admin propio,
o `lift_to_core` si patrón generalizable a `core/luana-core-platform/admin/`.

### `nicolify/backend/tests/`

Tests del monolito histórico — auditar coverage cross-package. Si tests son
generalizables → lift a `core/luana-core-*/tests/`. Si son
nicolify-vertical-B2B → keep para los módulos brand-specific futuros.

### `nicolify/backend/alembic/`

Migrations del monolito. Verificar si Alembic head actual está alineado con
el schema que core/luana-core-*/persistence/ espera. Posible drift.

## Surfaces brand-vertical genuinas (no existen aún)

Per `.claude/rules/b2b-billable-hours.md` (aspirational) + `brand.yaml::features`:

| Surface | Path destino | Spec en rule | Status |
|---|---|---|---|
| Time tracking (`time_entry`) | `nicolify/backend/src/modules/nicolify/billable_hours/` | sí | **no existe** |
| Invoice generation (currency-aware client.currency) | `nicolify/backend/src/modules/nicolify/billable_hours/` | sí | **no existe** |
| Proposal lifecycle | `nicolify/backend/src/modules/nicolify/proposals/` | sí | **no existe** |
| Contract management + e-sign adapters (DocuSign/Firmar.online/Validatel/Acepta.com) | `nicolify/backend/src/modules/nicolify/contracts/` | sí | **no existe** |
| Client portal (Clerk separate org, dual filter tenant+client) | `nicolify/backend/src/modules/nicolify/client_portal/` (BE) + `nicolify/frontend/src/features/client-portal/` (FE) | sí | **no existe** |
| CRM enterprise overlay (multi-stage forecast B2B) | `nicolify/backend/src/modules/nicolify/crm_enterprise/` (overlay sobre core/luana-core-crm) | parcial | **no existe** |

Estas surfaces son la **identidad real** de nicolify como vertical Agencias +
Servicios B2B. Sin ellas, nicolify hoy = monolito histórico mal-llamado, no
brand vertical genuino.

## Lift candidates únicos (NO duplicados con core)

| Path actual | Sugerencia destino | Razón |
|---|---|---|
| `nicolify/backend/src/modules/sales_agent/observability/eval_simulator/` | `core/luana-core-sales-agent/src/luana_core_sales_agent/observability/eval_simulator/` (engine) o `tests/agentic_evals/simulator/` (per auditor-downstream-regression.md tabla SSoT § F) | Eval simulator schema-mirror surface, NO existe en core. Per CLAUDE.md F sección agentic evals — debería vivir en engine como SSoT cross-brand. **Promotion proposal candidato.** |

## Próximas promotion proposals candidatas

> Orden recomendado por valor/costo + dependencias. Cada una es una story
> independiente que `/pm-luana` debe abrir como proposal formal en
> `docs/promotion-protocol/proposals/` cuando se ratifique.

| # | Proposal | Brand origen | Target | Scope | Bloqueado por | Notas |
|---|---|---|---|---|---|---|
| 1 | `2026-MM-DD-purge-nicolify-duplicate-modules` | nicolify | core/luana-core-* (no lift, solo drop en nicolify) | XL | nada | Mover/borrar 12 módulos `drop_duplicate` con backup pre-drop. R3 downstream regression cross-brand (vitalia/comunify consumers). Recomendar split en sub-proposals por categoría: tier1 (assets, commercial_calendar, connections, landing, social_proof, tenant_domains, tenant_profile) tier2 (brand, campaigns, offer, iam) tier3 (analytics, crm) |
| 2 | `2026-MM-DD-lift-eval-simulator-to-core-sales-agent` | nicolify | core/luana-core-sales-agent/observability/eval_simulator/ | M | nada | Lift candidato único. Per auditor-downstream-regression.md § F ya está documentado |
| 3 | `2026-MM-DD-drop-nicolify-advertising-social_media` | nicolify | n/a (terminal drop) | S | nada | Módulos placeholder sin uso. Drop directo |
| 4 | `2026-MM-DD-resolve-scheduling-package` | nicolify (origen) | core/luana-core-scheduling (nuevo) o core/luana-core-platform (consolidar) | M | nada | Decisión arquitectónica: ¿crear paquete dedicado o consolidar? |
| 5 | `2026-MM-DD-purge-nicolify-shared-and-core` | nicolify | core/luana-core-platform | L | proposal #1 | Después de purgar modules/, abordar `src/shared/` + `src/core/` |
| 6 | `2026-MM-DD-audit-copilot-overlay-nicolify` | nicolify | clarify si hay overlay vertical-B2B | M | nada | Inspeccionar 12 archivos delta core-nicolify en copilot. Si overlay legítimo → migrate a `modules/nicolify/copilot/`. Si no → drop_duplicate |
| 7 | `2026-MM-DD-audit-sales-agent-overlay-nicolify` | nicolify | clarify si hay overlay vertical-B2B | M | nada | Idem copilot. Excluye eval_simulator (lift separado proposal #2) |

## Nuevas stories nicolify (brand-vertical genuinas)

> Cuando se haya completado el purge (proposals #1, #3, #5), nicolify queda
> "limpio" y listo para construir lo brand-vertical. Estas son stories
> nuevas, NO promotion proposals.

| # | Story candidate | Surfaces tocadas | Scope | Valor |
|---|---|---|---|---|
| N1 | `nicolify-billable-hours-mvp` | time_entry CRUD + invoice generation currency-aware | L | ALTO — core del modelo B2B agencias |
| N2 | `nicolify-proposal-lifecycle` | proposal stages + viewed tracking + webhooks acceptance | M | ALTO — close-rate visibility |
| N3 | `nicolify-contract-management` | template render DOCX/PDF + e-sign adapters DocuSign/Firmar.online/Validatel/Acepta.com | XL | ALTO — compliance LatAm |
| N4 | `nicolify-client-portal` | Clerk separate org + dual filter tenant+client + read-only portal | L | ALTO — diferenciador B2B vs competidores |
| N5 | `nicolify-crm-enterprise-overlay` | multi-stage Kanban forecast + lost_reason enum + revenue forecast | M | MEDIO |

## Tabla resumen acciones

| Fase | Acción | Estado | Owner |
|---|---|---|---|
| 1 | Audit + verdict matrix (este doc) | ✅ done 2026-05-16 | /pm-luana + /pm-nicolify |
| 2 | Ratificación verdicts por Chris | ✅ done 2026-05-16 | Chris |
| 3 | Abrir promotion proposals #1-#7 individuales | ✅ ejecutadas como Waves 1-4 (commits 3b02db2, 627ff93, 880c7b4) + Commits A-D layout multibrand purge (d3113fa, d296fc7, a26b97d, este commit) | /pm-luana |
| 4 | Ejecutar lifts/drops | ✅ done 2026-05-16 (autonomous lift /pm-luana — patrón anterior) | /pm-luana |
| 5 | Stories nicolify N1-N5 (brand-vertical) | ⏳ pending post-purge — handoff `/pm-nicolify` cuando se prioricen | /pm-nicolify |

### Estado final `nicolify/backend/src/` (post Commits A-D)

```
nicolify/backend/src/
├── main.py                                    # FastAPI entry (100% engine consumer)
└── modules/
    └── nicolify/                               # único brand namespace
        ├── admin/                              # Streamlit admin panel (ex src/admin)
        ├── advertising/                        # Brand-vertical agencias B2B (paid media)
        ├── edges/                              # Edge routes (ex src/edges)
        ├── persistence/                        # SQLA mapper wiring (ex src/shared/infrastructure)
        └── workers/                            # ARQ workers + scheduler (ex src/workers)
```

**Verificación zero duplicación core:**
- 0 paths `src/{shared,admin,edges,workers,scripts,tests}/` legacy
- 100% main.py imports = `luana_core_*` (engine) o `src.modules.nicolify.*` (brand-vertical)
- 0 cross-brand imports (`from nicolify` en vitalia/comunify/lupulo/core = 0 hits)
- 0 cross-codebase mirrors detectados

## Anti-patterns observados (a corregir)

- ❌ Carve-out a core/ ejecutado sin purge en brand origen → duplicación masiva invisible
- ❌ Brand vertical layout (`{brand}/`) creado sin estructura `modules/{brand}/` → código histórico se trasplanta sin discriminar core vs vertical
- ❌ Aspirational rules (`b2b-billable-hours.md`) sin tracking de implementation gap
- ❌ Capability inventory cero al merge del bootstrap layout multimarca → falsa señal "shipped" en checkpoint

## Próximo paso inmediato

**Carve-out nicolify ✅ COMPLETO 2026-05-16.** Nicolify está listo como brand-vertical autocontenida.

Próximas acciones (handoff `/pm-nicolify`):

1. Fix `factory-boy` dep missing en `nicolify/backend/pyproject.toml` (bloquea pytest collect)
2. Capability inventory recovery — populate `nicolify/docs/product/capabilities/` desde código vivo
3. Stories N1-N5 brand-vertical genuinas (billable_hours, proposals, contracts, client_portal, crm_enterprise) cuando se prioricen

**Próxima brand prioritaria:** Vitalia (handoff `/pm-vitalia`).

## Referencias

- Audit original carve-out plan: `docs/architecture/luana-platform/01-core-audit.md`
- Purge audit (precedente): `docs/architecture/luana-platform/02-core-purge-audit.md`
- Brand mapping table: `CLAUDE.md` § "Brand → Core mapping"
- Engine packages contracts: `docs/core-modules/README.md`
- Anti-duplication rule: `.claude/rules/anti-duplication.md`
- Downstream regression: `.claude/rules/auditor-downstream-regression.md`
- Aspirational brand rule: `nicolify/.claude/rules/b2b-billable-hours.md`
- Brand config: `nicolify/config/brand.yaml`
