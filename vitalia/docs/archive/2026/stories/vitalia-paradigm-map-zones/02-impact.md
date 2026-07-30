<!-- voseo-allowed: inventario interno de impacto, no user-facing -->
# 02-impact — Inventario completo del cambio de taxonomía de agentes (definitivo)

> Story `vitalia-paradigm-map-zones` · opción (B) ratificada por Chris 2026-05-30: "este es el cambio nuevo y ÚLTIMO sobre agentes".
> Scan exhaustivo frontend + docs (2026-05-30). Este doc = SSoT de "qué cambia, dónde, a qué".

## 0. El cambio en una línea

`6 tabs (Lisa·Lucas·Adrián·Valeria·Camila + Configurar)` con Valeria=tab "Operar"+sidebar y Mateo="Tecnología" transversal
→ **5 especialistas (Lisa·Mateo·Adrián·Lucas·Camila) + Valeria=SOLO sidebar supervisor + Plataforma (acceso/onboarding/configuración) + Infraestructura (4 cajas)**.
Mateo **deja de ser "Tecnología"** y pasa a **"Operar/Mi Día"** (agenda + pacientes-del-día). Lo "técnico/IA" que Mateo representaba se disuelve en Infraestructura (motor-agentico) — no es un agente user-facing.

## 1. Resolución de las caps `agent_owner: valeria` (4)

| Cap | → box nuevo | functional_area nuevo |
|---|---|---|
| `scheduling/valeria-agenda.yaml` | **mateo** (Agentes) | `mateo.agenda` |
| `booking/booking-widget-embed.yaml` | **mateo** | `mateo.bookings` |
| `booking/prepaid-booking-advisory-locks.yaml` | **mateo** | `mateo.bookings` |
| `shell-organism/shell-vitalia.yaml` | **plataforma-tecnica** (Infra) | `plataforma-tecnica.shell` (el shell es contenedor, no agente; Valeria-chat es parte de él) |

Valeria NO queda como `agent_owner` de ninguna cap de valor (es supervisora — su runtime se documenta en `motor-agentico`).

## 2. Distribución caps `agent_owner: config` (22) → Plataforma + algunas a Infra·seguridad

| → box | Caps |
|---|---|
| **acceso** (Plataforma) | `auth/clerk-middleware`, `auth/sign-in-sign-up-pages`, `iam/iam-scaffold-slice-1`, `iam/luana-core-adoption` (4) |
| **onboarding** (Plataforma) | `onboarding/clinic-onboarding-3step`, `onboarding/wizard_brand_studio_slice_1`, `copilot/valeria-wizard-onboarding-agentic` (3) |
| **configuracion** (Plataforma) | `admin/{admin-streamlit-service,clinics-crud,streamlit-tenants-users,tenants-crud,users-crud}`, `clinics/clinics-brand-extension`, `connections/{oauth-meta-google-ads,registries-medical-vertical}`, `patients/patient-records-medical-history`, `fiscal/fiscal-emission-pe` (11) |
| **seguridad-cumplimiento** (Infra) | `compliance/{compliance-hipaa-lite-audit,hipaa-lite-defensive-stack,whatsapp-template-registry}`, `clinics/hipaa-dual-filter-decorator`, `audit/audit-writer-ssot` (5) — d3: enforcement técnico → Infra |

> Nota d3: la *vista* de compliance al cliente (story `lisa-compliance`, aún no construida) → Plataforma·configuracion; el *enforcement* (audit/dual-filter/cifrado) → Infra·seguridad. Las caps existentes son enforcement → Infra.

## 3. Distribución caps `agent_owner: infra` (22) → 4 cajas Infraestructura

| → box | Caps |
|---|---|
| **observabilidad** | `observability/{api-health-endpoint,otel-sentry-graceful-degradation,vitalia-callback-subclasses}` (3) |
| **plataforma-tecnica** | `platform/{design-tokens-foundation,design-tokens-theme,migrations-slice-1-schema,shell-foundation-shadcn-tailwind-v4,tenant-switcher,topbar-global,vertical-medical-extension-sdk}`, `payment/payment-gateways-latam-recurring`, `workers/idempotent-cron-arq-scaffold`, `ops/k8s-admin-deployment` (10) |
| **motor-agentico** | `agentic/{eval-goldens-slice-1,medical-agentic-tools,medical-safety-guardrails}`, `copilot/{medical-kb-rag,medical-pdf-extractors}`, `sales_agent/state-overlay-langgraph` (6) |
| **seguridad-cumplimiento** | `fixtures/3-clinic-fixture-latam` (1) |
| **(revisar)** | `ops/live-reconciliation-sweep`, `tests/playwright-smoke-suite` → plataforma-tecnica (scaffolding) (2) |

## 4. Caps especialistas vigentes (sin cambio de zona, quedan Agentes)

`lisa` (4) · `adrian` (7) · `lucas` (6) · `camila` (3) — solo se confirma su zona=agentes. Mateo gana las 3 ex-valeria (agenda+bookings).

## 5. Frontend (vitalia/frontend) — código shipped que cambia

| Archivo | Qué tiene hoy | Cambio |
|---|---|---|
| `src/lib/agent-catalog.ts` | `AGENT_CATALOG.valeria{label:"Operar",sub:agenda}` · `mateo{label:"Tecnología",sub:ia}` · `AGENT_RIBBON_ORDER=[lisa,lucas,adrian,valeria,camila]` · `RIBBON_SUBTABS.valeria=[agenda,pacientes]` · `mateo=[]` · `config=[cuenta,conexiones,avanzado]` | `AGENT_RIBBON_ORDER=[lisa,mateo,adrian,lucas,camila]` · Valeria fuera del ribbon (queda sidebar) · `mateo{label:"Operar",sub:agenda}` con `RIBBON_SUBTABS.mateo=[agenda,pacientes]` · Configurar→Plataforma |
| `src/components/shared/shell-organism/Ribbon.tsx` | renderiza `AGENT_RIBBON_ORDER` + `ConfigTab` | mismo render (lee del catalog) + ConfigTab→Plataforma label |
| `src/app/[tenantId]/(shell-organism)/valeria/` | carpeta routing valeria | renombrar/migrar a `mateo/` (agenda) |
| `src/app/[tenantId]/config/[subtab]/` | config routing | → plataforma (acceso/onboarding/configuracion) |
| `src/features/valeria/` | agenda (shipped) + pacientes | → `features/mateo/` (agenda) |
| `src/features/config/` | cuenta/conexiones/avanzado | → features plataforma |
| `src/app/globals.css` | `--agent-mateo` ya existe (#FEE209) | reutilizar (Mateo ya tiene color) |
| `public/agents/` | lisa,lucas,adrian,valeria,camila,mateo | Mateo ya tiene avatar ✓ · Valeria sigue (sidebar) |

> ⚠️ **Gate ADR-vitalia-003 (tu regla):** cualquier cambio visual del shell (Ribbon, sidebar) requiere **mockups por componente ratificados** ANTES de construir. → ticket de mockup en el plan `/architect`.

## 6. Cockpit (tools/luana-cockpit) — tool cross-brand

| Archivo | Hoy | Cambio |
|---|---|---|
| `lib/agent-meta.ts` | `AgentId` 7 (sin mateo) + `AGENTS` map | agregar mateo · render por zona |
| `lib/types.ts` | `AgentOwner` 7 (sin mateo) | agregar mateo · agregar `zone`/`map_box` |
| `components/map/MapView.tsx` | `FALLBACK_AGENTS` 6 (Valeria "Mi Día", config) | render por **zona** + 2 lentes · Valeria→supervisor sidebar · Mateo agente · leer `zones` de SYSTEM-MAP |

## 7. Docs / rules / skills / ADRs

| Archivo | Cambio |
|---|---|
| `vitalia/docs/architecture/ADR-vitalia-005-*` | → **v2.0** (5ª dim zona + enum boxes + config/infra deprecados + Valeria supervisor/Mateo Operar + §2.6 MapView por zona; `areas/` nunca construido → redefinir por zona o descartar) |
| `vitalia/docs/architecture/ADR-vitalia-004-*` | línea 75 Ribbon "6 agentes (…Valeria…Configurar)" → **addendum v1.2** "5 especialistas (Lisa·Mateo·Adrián·Lucas·Camila) + Plataforma" |
| `vitalia/docs/architecture/ADR-vitalia-003-*` | línea 22 lista agentes → ref menor |
| `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` | "6 agentes fijos" N1 Ribbon → 5 + Valeria sidebar |
| `docs/process/capability-protocol.md` §7 | tabla `agent_owner` (config/infra) → tabla v2 con boxes nuevas |
| `vitalia/CLAUDE.md` (overlay) | línea 81 "6 agentes" → 5 especialistas + Valeria supervisor + Mateo Operar |
| `.claude/skills/vitalia-design-system/SKILL.md` | "6 agentes", "Ribbon de 6 agentes", catálogo colores (Valeria/Mateo/Config) → actualizar |
| `vitalia/.claude/rules/shell-mockup-per-component.md` | "Ribbon 6 agentes" (líneas 58,68) + paleta (línea 130) → 5 + plataforma |
| `vitalia/.claude/rules/shell-feature-architecture-mandatory.md` | línea 39 `config-*` → plataforma-* |
| `vitalia/docs/product/modules/*.md` (23) | ref de zona/caja en headers (auto-list regenera) |
| MEMORY `vitalia-agents-catalog` + `vitalia-shell-organism-2026-05-21` | actualizar pointer (Valeria supervisor, Mateo Operar) |

## 8. Backlog Fase 2 — renombrar (d4)

| Story actual | → renombrar a |
|---|---|
| `vitalia-fase2-config-cuenta` | `vitalia-fase2-configuracion-cuenta` |
| `vitalia-fase2-config-conexiones` | `vitalia-fase2-configuracion-conexiones` |
| `vitalia-fase2-config-avanzado` | `vitalia-fase2-configuracion-avanzado` |
| `vitalia-fase2-config-onboarding-clinica` | `vitalia-fase2-onboarding-clinica` |
| `vitalia-fase2-valeria-pacientes` | `vitalia-fase2-mateo-pacientes` (pacientes del día, d2) |
| `vitalia-fase2-lisa-compliance` | queda Lisa (vista compliance al cliente, d3) |
| resto `adrian-/lucas-/camila-/lisa-*` | sin cambio (caja = agente) |

(+ una story UI nueva sugerida: `vitalia-shell-ribbon-realign` — pero en (B) va dentro de ESTA story con su mockup-gate.)

## 9. Riesgos de regresión (correr todo en paralelo)

1. Si `RIBBON_SUBTABS` mueve agenda a mateo pero las rutas/features siguen en `valeria/` → 404 silencioso. **Migrar catalog + routing + features juntos.**
2. Cockpit `FALLBACK_AGENTS` hardcoded mostraría Valeria "Mi Día" aunque sea sidebar → actualizar MapView.
3. Tests e2e que buscan `[aria-label="Operar"]` en tab Valeria → fallan (Valeria ya no tab). Actualizar specs.
4. Mockups archivados (Ribbon 6 tabs) son read-only históricos → NO editar; crear mockups nuevos para el shell realineado.
5. `agent-catalog.ts` es el SSoT del shell — todo (Ribbon, routing dispatcher, subtabs) deriva de él. Cambiarlo primero, propagar.

## 10. Conteo total de impacto

- **70 caps** (4 valeria + 22 config + 22 infra re-tag · 22 especialistas confirmar zona)
- **~13 docs/rules/skills/ADRs**
- **~8 archivos frontend** (agent-catalog, Ribbon, routing, features ×N, globals, cockpit ×3)
- **6 stories Fase 2** renombrar
- **+ mockups nuevos** del shell realineado (gate ADR-003)
- **+ tests** actualizar (e2e Ribbon/Valeria)
