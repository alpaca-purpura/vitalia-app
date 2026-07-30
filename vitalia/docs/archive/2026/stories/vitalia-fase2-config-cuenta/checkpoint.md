---
story_id: vitalia-fase2-config-cuenta
type: ui-story
agent_owner: configuracion
module: configuracion
capability: configuracion.cuenta
state: done
phase: MERGED                          # /pm-vitalia Fase F 2026-06-12 · cap configuracion.cuenta LIVE · SYSTEM-MAP live · 07-merge.md · archived R2
last_artifact: 07-merge.md
gherkin_matrix: 06-audit/gherkin-matrix.md
done_at: '2026-06-12'
next_action: "—"
dod_live_verified: true
dod_env: "localhost:3002 (FE) + :8002 (BE) · Playwright real-backend-forward + Clerk auth real (dr.demo) · NO mocks del surface"
dod_evidence:
  - action: "E2E browser SC-04: admin autenticado edita 'Nombre comercial' → autosave 600ms → PATCH /api/v1/clinics/account/ → reload → valor persiste → restore"
    observed: "PATCH 200 · data-state saved · reload refleja valor (DB persist) · audit_log_async_written action=clinic_account_patch clinic_id=f035be5b tenant_id=e69a691d ×2"
    backend_log: "PATCH /api/v1/clinics/account/ HTTP/1.1 200 OK · audit_log_async_written · sin traceback (docker logs 2026-06-12 01:02)"
  - action: "E2E SC-01/02/03/05/06: datos reales del tenant cargan (GET 200, no placeholder) · SubSubTabsBar N3 navega datos/preferencias/responsable · currency/timezone selectors · DPO link"
    observed: "6/6 specs passed · fixture anti-burbuja (0 console errors) · GET account/catalog/dpo 200"
    backend_log: "GET /api/v1/clinics/account/ 200 · /specialties-catalog 200 · /dpo 200"
  - action: "Curl negativo: PATCH primary_specialties=['no-existe'] → 422 (RN-3/AC-4b) · PATCH sin X-User-ID → 422 · rol no permitido → 403"
    observed: "validaciones fail-closed verificadas live"
    backend_log: "422/403 sin traceback"
verified_at: 2026-06-12
auditor_findings_preload:
  - id: F-RBAC-consistency
    severity: low-medium
    finding: "account_router check RBAC a mano en service vs Depends compartido require_brand_owner_access del sibling doctors_router. Enforce fail-closed OK. Consistencia/anti-dup → Carril R candidate."
  - id: F-engine-me-role-drift
    severity: medium · target /pm-luana
    finding: "ENGINE luana-core-iam GET /me devuelve users.role LEGACY GLOBAL, no user_tenants.role per-tenant (dr.demo: global=doctor vs per-tenant=owner). El docstring de useCurrentUser afirma lo contrario (doble-fuente que decía haber matado). Workaround brand: views config usan useTenants()/me/tenants (per-tenant correcto). Promotion proposal pendiente."
fix_session_2026-06-12:   # builders dejaron 5 bugs integración que el orchestrator cazó/arregló EJERCIENDO live (verification-real-not-200)
  - "ui-kit REGRESIÓN DEL LIFT 3cb9d5a0 (hoy): subSubTabsByKey nunca cableado ShellLayoutClient→AppPanelSlot + 'config' fuera de validSlugs → barra N3 NO se pintaba para NADIE (lisa/marca shipped también rota). Fix engine mínimo backward-compat (prop opcional) + wire vitalia AGENT_SUBSUBTABS."
  - "FE 422: account_router exige X-User-ID en TODAS las routes; fetchClient no lo manda → +userId header en api fns + useAccountQuery NEW (pages SSR pasan initialData=null y el view NUNCA fetcheaba → form siempre vacío, SC-11 roto)."
  - "FE payload camelCase IGNORADO silencioso por BE Pydantic snake (200 sin persistir) → keysToSnake decamelize boundary."
  - "BE 5xx: UUID(X-User-ID) con Clerk id → _resolve_audit_actor (patrón marca_router) · ClinicAccountPatchRequest sin campo name (autosave de nombre no persistía) · service loop sin 'name' · _WRITE_ROLES={admin_clinic} negaba al owner real → alineado a ALLOWED_BRAND_OWNER_ROLES {owner,admin_clinic} · validate_specialties NO EXISTÍA (RN-3/AC-4b sin enforce) → implementado +422."
  - "Catálogo specialties: BE emite {id,name,tier} vs arch decía string[] → FE alineado al shape rico (persiste id, muestra name) + SpecialtyEntryDTO."
  - "e2e spec HUÉRFANO: e2e/specs/config/ no matchea ningún project → movido a e2e/shell-organism/config-cuenta.spec.ts + smoke testMatch (falso-verde silencioso)."
  - "Infra: imagen FE stale post-lift @luana/format (tailwind-merge missing) → rebuild. El 'Clerk token expirado' del builder era DIAGNÓSTICO ERRADO (creds verificadas sanas contra API Clerk)."
architecture_pattern: ADR-vitalia-004
adr_004_compliance: partial-with-rationale
spec_round: 2
po_ux_version: 1.0-executable
ready_package:
  arch: 03-arch.md
  validators: 04-validators.yaml
  guidelines: 05-guidelines.md
  tickets: 06-tickets.yaml
  dispatch: dispatch-plan.md
ready_closed_by: architect
ready_closed_at: '2026-06-11T17:00:00Z'
state_opened_developing_at: '2026-06-11T18:05:00Z'
autonomous_mode: true                 # Chris override 2026-06-11 (ver D-AUTO) — full unattended hasta done
demo_required_override:
  overridden_to: false
  by: chris
  at: '2026-06-11T18:05:00Z'
  rationale: "Chris ratificó full-unattended hasta done. Waива el chris_verify.signoff humano. El auditor v5 SIGUE ejerciendo live-verify propio + poblando dod_evidence (piso técnico HARD, no waivable). dod_live_verify.required permanece true."
last_modified: '2026-06-11T18:05:00Z'
ratified_by_chris: true
ratified_visual_by_chris: true
ratified_at: '2026-06-11T14:30:00Z'
parallel_safe: true
priority: high
estimated_dev_days: 2-3
ratified_decisions:
  - id: D1
    date: 2026-06-07
    decision: "Billing/Plan Luana SACADO de esta story → defer a vitalia-pricing-decision + core billing (/pm-luana). Razón: pricing deferred (TIER 7) + modelo por-puesto/SKU (ADR-013 empleados-IA) + facturar SaaS es cross-brand (anti-duplication)."
    ratified_by: chris
  - id: D2
    date: 2026-06-07
    decision: "Equipo/RBAC (CRUD usuarios + roles + invite) SACADO → pertenece a la caja Acceso (SYSTEM-MAP absorbs config.iam); ya LIVE en admin Streamlit users-crud. config-cuenta = solo datos del tenant."
    ratified_by: chris
  - id: D3
    date: 2026-06-07
    decision: "Naming alineado a zona plataforma → caja configuracion → área cuenta. agent_owner/module/capability = configuracion(.cuenta), cap_change_type=new. Slug de carpeta sin cambio."
    ratified_by: chris
  - id: D3-revoked
    date: 2026-06-11
    decision: "Especialidades AHORA EDITABLES (revoca D3 read-only ratificado 2026-06-07). Tipo clínica sigue read-only. Implicación: +30% scope (specialty_catalog validators, PATCH endpoint, audit log, posible recalc agentes). Escalado a /architect para redesign."
    ratified_by: chris
  - id: D-AUTO
    date: 2026-06-11
    decision: "Full unattended hasta done. autonomous_mode=true (dev-team→auditor sin pausa G). demo_required override→false (waiva el chris_verify.signoff humano). Auditor v5 mantiene live-verify propio + dod_evidence (piso técnico no waivable). Aceptado el tradeoff de no firmar el demo live de datos fiscales/legales del tenant."
    ratified_by: chris
dependencies:
  hard:
    - vitalia-fase1-empty-states
    - vitalia-fase1-routing-shell
  soft:
    - vitalia-fase2-onboarding-clinica
blocks_hard: []
blocks_soft: []
reuse_map_summary: >-
  CONSUME core/luana-core-iam + clinics/ + fiscal/ validators + TenantLocale (master-data) ·
  EXTEND onboarding tenant_clinic_config (vista editable post-onboarding) ·
  NEW UI sub-tab Cuenta (hoy placeholder) · NO billing · NO equipo/RBAC
spawned_at: 2026-05-22T00:00:00.000Z
open_questions_resolved:
  by: /pm-vitalia
  at: '2026-06-11T18:00:00Z'
  Q1_fiscal_checksum: "MVP = formato + longitud SIEMPRE + checksum SOLO donde el algoritmo es estándar/estable (AR CUIT mód-11, UY RUT mód-11). PE RUC / MX RFC / CL-CO NIT = formato+longitud (sin checksum MVP). País no soportado → freetext degradado (NO bloquea)."
  Q2_specialty_catalog: "Curado brand-local en _shared/catalogs/specialty_catalog.py. Contenido inicial derivado de vision.md Tier 1-3 por país (AR/PE/MX/CL/CO/UY): odontología, medicina estética, oftalmología, psicología, psiquiatría, dermatología, nutrición clínica, fisioterapia, medicina capilar, fertilidad. Lift candidate documentado (NO lift 1ª impl)."
  Q3_dpo_source: "Leer tenant.config_json.compliance.dpo si existe; si ausente → empty state 'Aún no configurado' + link a config/seguridad. Read-only (se gestiona en Seguridad y cumplimiento)."
  Q4_config_route: "Confirmado NO colisiona. config = static segment real (mismo patrón que mateo/agenda SHIPPED_STATIC_SUBTABS). Builder crea ruta estática real; quitar config.cuenta del PLACEHOLDER_MAP + agregar a SHIPPED_STATIC_SUBTABS."
release: F4
cap_target: configuracion.cuenta
cap_change_type: new
parent_story: null
---

# F2-S20 vitalia-fase2-config-cuenta — checkpoint

> Scope ratificado 2026-06-07 (D1/D2/D3). Análisis pre-refinamiento + drift audit: `00-pm-analysis.md`.

## Goal

Área **Cuenta del tenant** de la caja **Configuración** (zona Plataforma · ribbon tab "Plataforma"). Vista user-facing de **uso poco frecuente** (admin) con los **datos del propio tenant/clínica**. Hoy es solo placeholder (`CuentaPlaceholder.tsx`); construir la vista real que **consume** el backbone ya existente (iam · clinics · fiscal · onboarding · audit), no rehacerlo.

## Anti-objetivos (ratificados)

- ❌ **NO billing / Plan Luana / Stripe** (D1 — defer a `vitalia-pricing-decision` + core billing vía `/pm-luana`).
- ❌ **NO equipo / RBAC / invite usuarios** (D2 — pertenece a caja Acceso; ya LIVE en admin Streamlit `users-crud`).
- ❌ NO recrear `core/luana-core-iam` ni `TenantLocale` (consumir vía import).
- ❌ NO re-capturar `vertical`/`primary_specialties` — los posee onboarding (read-only acá, decisión onboarding D3 2026-05-26).
- ❌ NO cambio de vertical post-onboarding (read-only · proceso support).

## Scope propuesto (4 secciones · /po-ux detalla AC + Gherkin + mockups)

### § 1 — Datos de la clínica (editable)
Nombre comercial · identificación fiscal country-specific (CUIT AR · RUC PE · RFC MX · NIT CL · RUT UY — **consume validadores de `fiscal/`**) · dirección · datos de contacto. `vertical` + `especialidades` = **read-only** (badge "definido en onboarding"). Autosave on-change.

### § 2 — Preferencias regionales
Timezone · idioma default (Spanish-LatAm) · moneda — vía `TenantLocale` VO (master-data). Sin hardcode.

### § 3 — Sedes (multi-clínica)
Lista de las sedes del tenant (consume `clinics/`). Read-only / light en MVP; CRUD de sede puede diferirse a story propia si crece.

### § 4 — Responsable de tratamiento / DPO
Contacto del data controller del tenant (HIPAA-lite obligación #8). *(Candidato a caja `seguridad-cumplimiento` — `/po-ux` confirma si vive acá o sólo se referencia.)*

### § 5 — Mobile
Secciones → accordion vertical (patrón shell).

## Pendiente /po-ux (no producir acá)
- `01-spec.md` con Gherkin AI-resistant (happy + negative + edge + adversarial) — incluir RN fiscal validator country-specific + RBAC lectura (solo admin_clinic edita) + audit log por cambio.
- Mockups HTML por componente (gate ADR-vitalia-003) ratificados por Chris ANTES de `refining → refined`.
- Matriz de cobertura + AC enumerados + Deliverables exactos.

## Reuse map (CONSUME-first)

| Origen | Qué | Adaptación |
|---|---|---|
| `core/luana-core-iam` | Tenant + User + Roles (scope lectura) | CONSUME |
| `vitalia/.../modules/vitalia/clinics/` | Sedes multi-clínica | CONSUME |
| `vitalia/.../modules/vitalia/fiscal/` | Validadores ID fiscal country-specific | CONSUME / EXTEND |
| onboarding `tenant_clinic_config` | vertical/especialidades/país/moneda | EXTEND (vista editable) |
| `TenantLocale` (master-data) | timezone/idioma/moneda | CONSUME |
| `audit/` + hipaa-lite | audit log por cambio | CONSUME |
| Shadcn | Tabs · Form · Table · Badge | reuse |

## Dependencies
- **Hard:** `vitalia-fase1-empty-states` · `vitalia-fase1-routing-shell`
- **Soft:** `vitalia-fase2-onboarding-clinica` (provee `tenant_clinic_config`)

## Riesgos
| Riesgo | Prob | Impacto | Mitigación |
|---|---|---|---|
| Fiscal validator por país incompleto | Media | Medio | Reusar `fiscal/`; cubrir AR/PE/MX/CL/UY; resto degradado a formato libre |
| Lockout edición (RBAC) | Baja | Medio | Solo `admin_clinic` edita; lectura para roles autorizados |
| Solape sedes con clinics module | Baja | Bajo | Read-only en MVP; CRUD difiere |

## Referencias
- `00-pm-analysis.md` — drift audit + propuesta (este turno)
- `vitalia/docs/architecture/SYSTEM-MAP.yaml` — zona plataforma → caja configuracion → área cuenta
- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` · `ADR-vitalia-004` · `ADR-vitalia-003`
- `vitalia/.claude/rules/hipaa-lite.md` — RBAC + audit + DPO
