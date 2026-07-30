---
story_id: vitalia-fase2-config-conexiones
type: ui-story
agent_owner: config
module: connections
capability: config.conexiones
state: idea
architecture_pattern: ADR-vitalia-004
last_modified: 2026-05-22
ratified_by_chris: false
parallel_safe: true
priority: high
estimated_dev_days: 5-6
dependencies:
  hard:
    - vitalia-fase1-empty-states
    - vitalia-fase1-routing-shell
  soft: []
blocks_hard: []
blocks_soft:
  - vitalia-fase2-adrian-inbox               # WhatsApp/IG/Email providers consumidos
  - vitalia-fase2-lucas-lanzar               # Meta/Google OAuth consumidos
  - vitalia-fase2-camila-reputacion          # Google MyBusiness / IG mentions
reuse_map_summary: "REUSE connections module shipped + nicolify HUB pattern · NEW UI 6 categorías + N3-dyn provider detail · NEW OAuth flows per provider · NEW health + actividad · NEW desconectar audit"
spawned_at: 2026-05-22
next_action: "/po-ux refinar 01-spec.md con wireframes HUB 6 categorías + provider detail drawer"

# Schema v2 migration (cement 2026-05-27)
release: F4   # release ID · ver releases/
cap_target: config.conexiones   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F2-S21 vitalia-fase2-config-conexiones — checkpoint

## Goal

Sub-tab Conexiones de Configurar: HUB integraciones cross-tenant. 6 categorías per navigation-tree:
1. **Marketing & Publicidad** — Meta Ads · Google Ads · TikTok Ads
2. **Mensajería & Atención** — WhatsApp Business API · IG DM · Telegram · Email SMTP/SES
3. **Pagos & Facturación** — Stripe · MercadoPago · payment-adapter-mvp · fiscal-emission services
4. **Calendarios externos** — Google Calendar · Apple iCal · Outlook
5. **Presencia Online** — Google MyBusiness · IG · TikTok · web embed
6. **Integraciones técnicas** — Zapier · n8n · APIs custom

UI: grid providers per categoría + drawer detalle per provider con OAuth · health · permisos · config · actividad log · desconectar.

## Anti-objetivos

- NO duplicar engine connections (`core/luana-core-channels` + per-brand extensions)
- NO implementar provider new no existing (story dedicada per provider future)
- NO duplicar payment adapters (consume payment-adapter-mvp service-story)

## Scope verbatim

### § 1 — Page + 6 categorías

`<ConfigConexionesView>` con tabs per categoría O grid 6-card top + provider grids dentro.

### § 2 — `ProviderCard`

Per provider:
- Logo + nombre
- Status: 🟢 Connected · 🟡 Warning · 🔴 Disconnected · ⚫ Not configured
- Last sync timestamp
- Click → drawer N3-dyn detail

### § 3 — N3-dyn `[provider-id]` drawer

Tabs:
- **OAuth** — Login flow / Re-auth / token expiry status
- **Health** — Last successful sync · error rate · uptime
- **Permisos** — Scopes granted · permissions requested
- **Config** — Per-provider settings (e.g., Meta Business ID · Google Calendar ID · IG account selector)
- **Actividad** — Log eventos (sync · errors · webhooks · disconnections)
- **Desconectar** — Confirm dialog · revoke OAuth · audit log

### § 4 — OAuth flow

Cada provider:
- Click "Conectar" → redirect provider OAuth (server-side state token)
- Callback `/api/connections/oauth/callback?provider=X&code=Y` → backend exchange code for token · audit · success redirect

Backend `vitalia/backend/src/modules/vitalia/connections/application/oauth_handler.py` per provider strategy.

### § 5 — Webhooks validation

Per `hipaa-lite.md`: webhooks validados con HMAC + timestamp window 5min.

### § 6 — Mobile

Cards grid responsive.

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | Page renderiza 6 categorías con providers |
| AC-2 | Status badges live per provider |
| AC-3 | Drawer detalle 6 tabs funcional |
| AC-4 | OAuth flow completo end-to-end per provider |
| AC-5 | Token refresh background worker |
| AC-6 | Webhooks HMAC validation funcional |
| AC-7 | Desconectar revoke + audit |
| AC-8 | Visual goldens × 8 (categorías + drawer × 2 themes) |
| AC-9 | a11y axe pass |
| AC-10 | Cross-tenant + RBAC (admin_clinic only edita) |
| AC-11 | Vitest + Playwright + a11y pass |

## Gherkin scenarios

### Scenario 1 — happy: conectar Meta Ads

**Given:** Tenant sin Meta Ads connection

**When:**
1. Click ProviderCard Meta Ads → "Conectar"
2. Redirect Meta OAuth
3. User approves
4. Callback → backend exchange · audit · success

**Then:**
- Connection persisted (token encrypted at-rest)
- Status badge 🟢 Connected
- Webhook subscribed
- Drawer activity log: `oauth_completed`

### Scenario 2 — edge: token expirado

**Given:** Connection Google Ads token expirado

**When:** Cron token refresh fails

**Then:**
- Status badge → 🔴 Disconnected
- UI alert "Reconectar Google Ads"
- Drawer detalle muestra error + CTA re-auth

### Scenario 3 — adversarial: webhook sin HMAC valido

**Given:** Adversarial sends webhook payload sin HMAC valido

**When:** Backend recibe

**Then:** Reject 401 · audit `webhook_invalid_hmac` · Sentry alert

### Scenario 4 — adversarial: desconectar cross-tenant

GET DELETE provider de otro tenant → dual filter 404 · audit.

### Scenario 5 — keyboard-a11y

Tab providers + drawer.

## Deliverables

| File | Acción |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/config/conexiones/page.tsx` | MODIFY |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/config/conexiones/[provider-id]/page.tsx` | NEW (N3-dyn) |
| `vitalia/frontend/src/features/config/components/conexiones/ConfigConexionesView.tsx` | NEW |
| `vitalia/frontend/src/features/config/components/conexiones/CategoriaSection.tsx` | NEW (per categoria) |
| `vitalia/frontend/src/features/config/components/conexiones/ProviderCard.tsx` | NEW |
| `vitalia/frontend/src/features/config/components/conexiones/ProviderDetailDrawer.tsx` | NEW |
| `vitalia/frontend/src/features/config/components/conexiones/tabs/{OAuth,Health,Permisos,Config,Actividad,Desconectar}Tab.tsx` | NEW (6 files) |
| `vitalia/frontend/src/features/config/api/conexiones.ts` | NEW |
| `vitalia/frontend/src/features/config/types/connection.types.ts` | NEW |
| `vitalia/backend/src/modules/vitalia/connections/api/conexiones_router.py` | MODIFY |
| `vitalia/backend/src/modules/vitalia/connections/api/oauth_callback_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/connections/application/oauth_handler.py` | NEW (per-provider strategy) |
| `vitalia/backend/src/modules/vitalia/connections/application/token_refresh_worker.py` | NEW (cron) |
| `vitalia/backend/src/modules/vitalia/connections/application/webhook_validator.py` | NEW (HMAC + timestamp) |
| `vitalia/backend/src/modules/vitalia/connections/persistence/migrations/XXXX_connections_tokens.py` | NEW (idempotent + pgcrypto encrypted token col) |
| `vitalia/frontend/e2e/shell-organism/config-conexiones-oauth.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/conexiones/{view}-{light\|dark}.png` (×8) | NEW |
| `vitalia/backend/tests/modules/vitalia/connections/test_oauth_flow.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/connections/test_token_refresh.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/connections/test_webhook_hmac_validation.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/connections/test_conexiones_cross_tenant.py` | NEW |

## Reuse map

| Origen | Componente / pattern | Adaptación |
|---|---|---|
| `core/luana-core-channels` (engine) | ChannelAdapterDef registry | CONSUME via EP-X |
| Vitalia shipped — `vitalia/backend/src/modules/vitalia/connections/` | Connections base | EXTEND |
| Nicolify HUB pattern | Provider grid + drawer detail | TRANSPONER 80% |
| Shadcn primitives | `Sheet` · `Tabs` · `Card` · `Dialog` · `Switch` · `Badge` | reuse |

## Dependencies map

### Hard
- `vitalia-fase1-empty-states` + `vitalia-fase1-routing-shell`

### Soft
- ninguna

### Esta historia desbloquea
- F2-S3 adrian-inbox: WhatsApp/IG/Email tokens
- F2-S15 lucas-lanzar: Meta/Google Ads tokens
- F2-S14 camila-reputacion: Google MyBusiness · IG mentions tokens

## Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| OAuth flows complejos per provider | Alta | Medio | Strategy pattern + per-provider tests |
| Token encryption at-rest gap | Baja | Crítico | pgcrypto column-level + key rotation policy |
| Webhook spoofing | Baja | Crítico | HMAC + timestamp window + IP allowlist optional |
| Token refresh worker fail silent | Media | Alto | Alerts + UI badge degradation visible |

## Definición de "Done"

1. AC verificados
2. Visual goldens × 8
3. Backend tests OAuth + token + webhook + cross-tenant pass
4. Story pushed + handoff `/auditor`
5. Auditor APPROVED → merge → capability `config.conexiones` registrada

## Próximo paso post-done

- F2-S3, F2-S15, F2-S14 consume tokens
- F2-S22 avanzado puede integrar API tokens externos

## Referencias

- **Design Contract:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- **Navigation tree:** § config.conexiones (6 categorías)
- **HIPAA-lite:** `vitalia/.claude/rules/hipaa-lite.md`
- **Engine channels:** `core/luana-core-channels`
- **Nicolify HUB pattern:** reuse reference
