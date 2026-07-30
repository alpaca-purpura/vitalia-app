# 00-pm-analysis · vitalia-fase2-config-cuenta

> PM análisis pre-refinamiento (`/pm-vitalia`, 2026-06-07). Drift audit + propuesta de scope grounded en visión + paradigma + SYSTEM-MAP. **NO es el spec** (eso lo produce `/po-ux`). Esto fija qué entra antes de refinar.

## 1 · Estado real (qué hay vs qué dice la story)

La story tiene un `checkpoint.md` rico (scope/AC/Gherkin/deliverables completos) pero **nunca pasó por `/po-ux`**: no hay `01-spec.md` ni mockups, y `chris-input.md` está vacío. State `refining` es nominal — el contenido es un draft de PM viejo (2026-05-22), no spec ratificada.

### "Ya avanzamos pero no se muestra" — confirmado, es drift de superficie

Lo construido relacionado a "Cuenta del tenant" existe pero **NO está cableado en la caja Configuración del shell**:

| Pieza relacionada | Dónde vive hoy | Estado |
|---|---|---|
| Sub-tab Cuenta en el shell | `features/config/components/placeholders/CuentaPlaceholder.tsx` (vía `SubTabContent.tsx` dispatcher) | **Solo placeholder** — no hay `config/cuenta/page.tsx` real |
| Users + roles + Clerk invite | `admin/` Streamlit (`admin/users-crud.yaml` **LIVE**) + `iam/` (user.py·role.py·resolvers) | Existe, pero **solo en panel admin interno**, no en el shell del tenant |
| Datos clínica (vertical·país·moneda·especialidades) | `onboarding` (cap `clinic-onboarding-3step` deprecated→reconstruida) + onboarding-clinica story | Capturados en alta; **falta vista editable post-onboarding** |
| Identificación fiscal country-specific | módulo `fiscal/` (fiscal_document, emit port) + `payments/fiscal_doc_type` | Existe a nivel doc fiscal; **no hay validador CUIT/RUC/RFC para datos del tenant** |
| Audit log + compliance | `audit/` + `compliance/` módulos | Existe (HIPAA-lite) |
| Multi-clínica (sedes) | `clinics/` módulo | Existe BE |

**Conclusión:** el backbone está disperso (admin panel + onboarding + iam + fiscal). Lo que falta es la **vista user-facing de "Cuenta del tenant" en la caja Configuración** que consuma esas piezas. No hay que construir casi nada de cero en BE.

## 2 · Drifts detectados (5)

1. **Zona/naming legacy.** `checkpoint.md` usa `agent_owner: config` · `module: tenant_account` · `cap_target: config.cuenta` · `cap_change_type: null`. La autoridad (SYSTEM-MAP.yaml + ADR-vitalia-004 v1.2 + paradigma 3-zonas) ubica esto en **zona `plataforma` → caja `configuracion` → área `cuenta`**, ribbon tab **"Plataforma"**. Convención de cap (ver `admin/users-crud.yaml`): `functional_area: configuracion.cuenta`. → corregir frontmatter + `cap_change_type: new`.

2. **Migración pendiente declarada.** `SYSTEM-MAP.yaml` (líneas 42-44) dice que las superficies de config/infra **todavía viven en cajas legacy** y su promoción a las zonas plataforma/infra es "story dedicada pendiente". config-cuenta es la primera caja `configuracion` que se construye real → decide si esta story también hace la promoción de naming o solo fija su cap correcto.

3. **"Plan Luana / Stripe billing" — premature + cross-brand + contradice visión.** El § 3 del draft mete dashboard de facturación SaaS (Free/Pro/Enterprise + Stripe). Pero: (a) `vitalia-pricing-decision` está en `idea`/F8, TIER 7 **DEFERRED** (pricing no decidido, placeholders en brand.yaml); (b) la visión ratificada (ADR-013 empleados-IA) cobra **por puesto/SKU**, no tiers SaaS; (c) facturar el SaaS es concern **cross-brand** (toda marca cobra) → `core/luana-core-billing` + `/pm-luana`, no una story de marca (anti-duplication: si va acá, las 10 marcas lo espejan).

4. **Equipo/RBAC — triple solapamiento.** El § 4 del draft (team CRUD + roles + invite) solapa con: (a) `admin/users-crud.yaml` LIVE, (b) `lisa-doctores` (developing, staff clínico), (c) la caja **`acceso`** del SYSTEM-MAP que absorbe `config.iam` (quién entra + qué puede). Gestionar usuarios/roles es naturalmente **Acceso**, no Configuración→Cuenta.

5. **Info clínica solapa onboarding-clinica.** `vertical` + `primary_specialties` los captura onboarding (read-only después, decisión D3 ratificada 2026-05-26). config-cuenta debe **consumir/editar** la tabla `tenant_clinic_config`, no crear una nueva ni re-capturar vertical.

## 3 · Qué debería ir en "Configuración → Cuenta" (propuesta grounded en visión)

Paradigma: caja Configuración = "ajustes del espacio" de uso **poco frecuente** (admin). Área Cuenta = **los datos del propio tenant/clínica**, no quién lo opera ni cómo se paga. Propuesta lean:

- **Datos de la clínica** (editable post-onboarding): nombre comercial · identificación fiscal country-specific (consume validadores `fiscal/`) · dirección · contacto. `vertical`/`especialidades` = **read-only** (los posee onboarding).
- **Preferencias regionales**: timezone · idioma · moneda — vía `TenantLocale` (master-data, NO recrear).
- **Sedes (multi-clínica)**: lista de las sedes del tenant (consume `clinics/`), light. CRUD de sede puede diferirse.
- **Responsable de tratamiento / DPO** (HIPAA-lite obligación #8): contacto del data controller del tenant. *(candidato a caja `seguridad-cumplimiento` — ver decisión).*

**Fuera de esta story:** facturación SaaS (→ defer/`/pm-luana`) · equipo+roles (→ caja Acceso o reusar admin) · cambio de vertical (→ onboarding/support).

Resultado: story chica (≈2-3 días), 100% consume BE existente, surface real en la caja que hoy es placeholder.

## 4 · Decisiones que necesito de Chris (bloquean el refinamiento)

- **D1 — Billing:** ¿saco "Plan Luana/Stripe" de esta story (defer a pricing-decision + core billing) o lo mantenés acá?
- **D2 — Equipo/RBAC:** ¿config-cuenta = solo datos del tenant (saco equipo), y team/roles van a su propia superficie (caja Acceso) / reusan admin? ¿O mantengo equipo acá?
- **D3 — Naming/zona:** ¿alineo frontmatter+cap a `configuracion.cuenta` (zona plataforma) en esta story, o lo dejo legacy y solo fijo el cap target?

Tras D1-D3 → update checkpoint + handoff `/po-ux` para 01-spec + mockups.
