---
story_id: vitalia-fase2-config-cuenta
brand: vitalia
type: ui-story
state: refined
architecture_pattern: ADR-vitalia-004
spec_round: 2
po_ux_version: 1.0-executable
input_spec_signed: true
mockup_final_signed: true
signed_at: 2026-06-11T14:30:00Z
signed_by: chris
---

# 01-spec · vitalia-fase2-config-cuenta — Cuenta del tenant

> **RONDA 2 (ejecutable · ratificada).** Spec completa lista para `/architect` → `03-arch.md`. Gherkin AI-resistant · matriz cobertura · AC enumerados · deliverables exactos. Mockup final ratificado en `mockups/cuenta.html`.

## § Context — Dónde vive

- **Zona → caja → área** (árbol `paradigm-arquitectura.md` + `SYSTEM-MAP.yaml`): zona **Plataforma** → caja **Configuración** → área **Cuenta del tenant**.
- **Shell** (`SHELL-DESIGN-CONTRACT.md`): ribbon tab **"Plataforma"** (slug URL `config`) → SubTabsBar → sub-tab **"Mi cuenta"** (🏢, default del tab).
- **Ruta donde aterriza el user:** `/{tenantId}/config/cuenta`. Hoy renderiza `CuentaPlaceholder.tsx` vía dispatcher dinámico `[agent]/[subtab]`. Esta story reemplaza el placeholder por la vista real.
- **Frecuencia de uso:** baja (admin) — paradigma: Configuración = ajustes del espacio, no operación diaria.
- **Release:** F4.

### Out-of-scope (anti-creep, ratificado)
- ❌ Facturación SaaS / Plan Luana / Stripe (D1 → `vitalia-pricing-decision` + core billing).
- ❌ Equipo / usuarios / roles / invite (D2 → caja Acceso; ya LIVE en admin Streamlit).
- ❌ Cambio de `vertical`/especialidades (read-only; los posee onboarding).
- ❌ Historia clínica / PHI de pacientes (otra caja).

## § Prior art applied

- **Engine consumed:**
  - `core/luana-core-tenant-profile` — perfil del tenant + `business_types_catalog` (vertical) + cambio rate-limited de business_types. **CONSUME** (no recrear).
  - `core/luana-core-iam` — tenant + roles (scope lectura/permiso de edición).
  - `core/luana-core-platform` `TenantLocale` VO — currency + timezone (NO tiene idioma — ver duda Q5).
- **Reused brand (vitalia, ya construido):**
  - `vitalia/.../modules/vitalia/clinics/domain/clinic.py` — entidad `Clinic` con `name · slug · country · timezone · plan_tier · is_active · onboarding_completed`. **EXTEND** (vista editable; faltan fiscal_id/address/idioma).
  - `clinics/application/credential_validator.py` + `credential_country.py` — patrón validación country-specific (referencia para validador fiscal).
  - `vitalia/.../modules/vitalia/fiscal/` — emisión fiscal (doc fiscal). **No** hay validador de ID fiscal del *tenant* → net-new acotado.
  - Stories archivadas: `vitalia-slice-1-onboarding-wizard` · `vitalia-fase1-tenant-switcher` (patrón tenant data) · `vitalia-fe-tenant-resolution-no-clerk-org` (tenant_id desde `useTenantId()`, NUNCA Clerk org).
- **Learnings aplicados:**
  - `vitalia/docs/learnings/2026-05-31-e2e-mockeado-verde-falso.md` — e2e NO mockea el BE de la superficie (live-verify real).
  - `vitalia/docs/learnings/2026-05-27-fase2-first-story-shipped-shell-feature-pattern.md` — patrón sub-tab ADR-004.
- **Lift candidates:** "Cuenta del tenant" (datos legales+fiscal+locale) es plausiblemente cross-brand → marcar como promotion candidate a `core/luana-core-tenant-profile` si comunify/nicolify lo replican. NO lift ahora (1ª implementación).
- **Net-new justificado:** campos `fiscal_id` (country-specific) + `address` + `idioma` no existen hoy en `Clinic`; validador de ID fiscal del tenant (CUIT/RUC/RFC/NIT/RUT).

## § Mapa funcional (DRAFT — sujeto a interrogatorio gate)

### Happy path (narrado)
1. Admin entra a Plataforma → Mi cuenta. Ve los datos de su clínica precargados (nombre, país, vertical read-only, fiscal, dirección).
2. Corrige un dato (ej. dirección o razón social) → autosave on-change → toast "Guardado".
3. Ajusta preferencias regionales (timezone / idioma / moneda) → autosave → la app refleja el cambio (formato fecha/moneda).
4. (si multi-sede) Ve la lista de sedes de su clínica; entra a una para ver/editar sus datos.
5. Revisa/edita el contacto del Responsable de tratamiento (DPO).
6. Todo cambio queda en audit log (HIPAA-lite).

### Estructura ratificada (RONDA 1 · Q1-Q5)
N3-static `SubSubTabsBar` con **3 sub-sub-tabs**: `/config/cuenta/{datos,preferencias,responsable}`.
1 clínica por tenant (**sin** sección Sedes — diferida). Idioma **derivado del país** (read-only). DPO = **solo referencia** (se gestiona en Seguridad y cumplimiento).

### Bifurcaciones (árbol)
```
N3 · Datos de la clínica (editable · autosave)
├─ ID fiscal formato inválido para el país → inline error + NO persiste                 [SC-neg]
├─ rol NO admin_clinic → campos read-only / 403 al guardar                              [SC-adv]
├─ tipo de clínica + especialidades → read-only (badge "definido en el alta")           [SC-edge]
├─ país → read-only (badge "definido en el alta"; cambio = soporte)                      [SC-edge]
└─ editar nombre/razón social/CUIT/dirección/contacto OK → autosave + persiste + audit   [SC-happy]
N3 · Preferencias regionales
├─ cambio timezone/moneda → autosave + re-render formatos fecha/moneda en la app         [SC-happy]
└─ idioma → derivado del país, read-only (cambio = soporte)                              [SC-edge]
N3 · Responsable de datos (referencia)
└─ ver DPO + link "Gestionar en Seguridad y cumplimiento ↗" (no edita acá)               [SC-happy]
```

### Reglas de negocio (DRAFT)
- **RN-1** Solo rol `admin_clinic` edita; otros roles autorizados ven read-only.
- **RN-2** ID fiscal validado por país (AR CUIT · PE RUC · MX RFC · CL/CO NIT · UY RUT); inválido → rechazo backend + inline error.
- **RN-3** `vertical` + `primary_specialties` read-only post-onboarding (cambio = proceso support).
- **RN-4** Todo write a datos del tenant → audit log sync pre-response (hipaa-lite).
- **RN-5** Datos del tenant son tenant-scoped (`tenant_id`); cross-tenant → 404.
- **RN-6** Preferencias regionales no se hardcodean; vienen de `TenantLocale` / tenant-profile.

### Criterios de aceptación (DRAFT)
- **AC-1** La sub-tab "Mi cuenta" muestra datos reales del tenant (no placeholder).
- **AC-2** Editar + autosave persiste y sobrevive recarga.
- **AC-3** Validación fiscal country-specific funciona (válido guarda, inválido bloquea).
- **AC-4** Read-only correcto para vertical + para roles no-admin.
- **AC-5** Audit log registra cada cambio.
- **AC-6** Live-verify real en dev-app (write ejercido + efecto + logs).

## § Wireframes (BORRADOR — RONDA 1)

- **Mockup borrador:** `mockups/cuenta.html` (wrapper shell portado verbatim de `_shared.css` + ribbon v1.2 Plataforma activa + N3 Datos·Preferencias·Responsable navegables). Servir: `cd mockups && python3 -m http.server 8888` → `http://localhost:8888/cuenta.html`.
- Átomos reales usados (NO inventados): `.card`/`.card-title`, `.field-row`, `.label`+`input`/`select`, `.chip`/`.chip-primary`/`.chip-warning`, `.subsubtabs-bar`/`.subsubtab-btn`, `.section-header`. Tokens = espejo de `globals.css` (vía `_shared.css`).
- Pendiente RONDA 2: estados (vacío/cargando/error/guardando), validación inline fiscal, microcopy final, mockup FINAL por sub-sub-tab.

## § Dudas resueltas + ratificadas (interrogatorio gate completo — RONDA 2)

### RONDA 1 (ratificado Chris 2026-06-07)
- **Q1 (layout): N3-static** — SubSubTabsBar 3 tabs (Datos · Preferencias · Responsable). No Shadcn Tabs body (anti-pattern Nivel 4). ✓
- **Q2 (sedes): 1 clínica** — sin sección Sedes; multi-sede diferido a story propia. ✓
- **Q3 (campos net-new): fiscal_id + dirección AHORA** (migración idempotente + validador country-specific AR/PE/MX/CL/UY). Idioma → derivado del país. ✓
- **Q4 (DPO): solo referencia** — se muestra + link a Seguridad/Cumplimiento; la edición vive allá. ✓
- **Q5 (idioma): derivado del país, read-only** en MVP (cambio = soporte). ✓

### RONDA 2 (ratificado Chris 2026-06-11)
- **Q6 (país): read-only** (definido en el alta; cambia → soporte). Formato fiscal + compliance amarrados al país. ✓
- **Q7 (razón social): separada** de nombre comercial (nombre comercial = mercado; razón social = fiscal/legal). ✓
- **Q8 (moneda): editable** (clínica puede operar en múltiples monedas; facturación = moneda del paciente). ✓

### Decision D3-revoked (ratificado Chris 2026-06-11 · post-ratificación visual)
- **Especialidades: AHORA EDITABLES** (fue read-only en D3, se revoca). Admin edita especialidades del tipo clínica actual. Implicación: validates contra specialty_catalog + audit log + posible recalc agentes. Scope +30%.
- **Tipo de clínica: sigue read-only** (cambio = soporte, compliance-crítico).

## § Gherkin (AI-resistant) — Escenarios por sub-sub-tab

### DATOS DE LA CLÍNICA

```gherkin
Escenario: Admin edita nombre comercial
  Dado que soy administrador de la clínica
  Y estoy en "Plataforma › Configuración › Mi cuenta › Datos"
  Cuando escribo un nuevo nombre comercial
  Y la vista autosave ejecuta (600ms)
  Entonces el nombre persiste en DB + audit log registra el cambio
  Y veo toast "Guardado" + FloatingAutosaveIndicator fade-out

Escenario: ID fiscal inválido por país (negativo)
  Dado que soy administrador
  Y el país es Argentina (CUIT obligatorio)
  Cuando escribo "XX-invalid-xx" en el campo CUIT
  Y intento autosave
  Entonces el backend rechaza con código de validación fiscal
  Y veo inline error rojo bajo el campo "Formato CUIT (Argentina) no válido"
  Y el cambio NO persiste (autosave abortado)

Escenario: Rol no admin_clinic intenta editar (adversarial)
  Dado que soy médico tratante (NO admin_clinic)
  Y abro la sub-tab "Datos"
  Entonces VISTO todos los campos read-only (sin `input`, sin `select` editables)
  Y veo chip amarillo "🔒 Solo el Administrador puede editar"
  Y POST a PATCH /tenant/clinic endpoint retorna 403 Forbidden

Escenario: País + Tipo clínica + Especialidades son read-only
  Dado que soy admin_clinic
  Y veo la sección "Identidad" en "Datos"
  Entonces Tipo clínica y Especialidades muestran badge "definido en el alta" + NO son editables
  Y País muestra badge "definido en el alta" + NO es editable (seleccionable tipo)

Escenario: Dirección + Teléfono + Email editables
  Dado que soy admin_clinic
  Cuando edito dirección / teléfono / email
  Y autosave
  Entonces los cambios persisten + audit log registra
  Y NO hay validación de formato estricta (freetext permitido)
```

### PREFERENCIAS REGIONALES

```gherkin
Escenario: Cambio de timezone
  Dado que soy admin_clinic
  Y estoy en "Preferencias"
  Cuando cambio de "America/Argentina/Buenos_Aires" a "America/Lima"
  Y autosave
  Entonces la zona horaria persiste en TenantLocale
  Y fechas mostradas en toda la app reflejan la nueva zona (ej. timestamp de auditoría)
  Y veo toast "Guardado"

Escenario: Cambio de moneda
  Dado que soy admin_clinic
  Y la clínica usa ARS
  Cuando cambio moneda a USD
  Y autosave
  Entonces currency persiste en TenantLocale
  Y montos mostrados reflejan la nueva moneda en formato y símbolo (ej. $100 → US$ 100)

Escenario: Idioma es read-only
  Dado que estoy en "Preferencias"
  Entonces veo Idioma = "Español (LatAm)" con badge "se deriva del país"
  Y NO puedo editarlo (campo read-only)
  Y aclaración: "Si necesitas otro idioma, escribe a soporte"
```

### RESPONSABLE DE DATOS

```gherkin
Escenario: Ver DPO con link a Seguridad/Cumplimiento
  Dado que soy admin_clinic
  Y estoy en "Responsable de datos"
  Entonces VISTO el nombre del DPO actual (ej. "Dra. Carla López")
  Y email + rol "Responsable de tratamiento (DPO)"
  Y link "Gestionar en Seguridad y cumplimiento ↗" navega a /config/seguridad

Escenario: No puedo editar DPO acá
  Dado que estoy en "Responsable de datos"
  Entonces es SOLO lectura (sin formulario de edición)
  Y aclaración: "Acá solo lo ves para referencia"
```

## § Matriz de cobertura (Bifurcación → Scenario → Verificación REAL)

| N | Bifurcación | Scenario GH | Verificación | AC |
|---|---|---|---|---|
| 1 | Happy path autosave + persist | Admin edita nombre comercial | write real + POST 200 + DB reflect + audit log row + toast visible | AC-1, AC-2, AC-5 |
| 2 | Validación fiscal invalid | ID fiscal format invalid → 400 + inline error | write real CUIT invalid + endpoint rechaza + UI error visualiza + NO persist | AC-3, AC-6 |
| 3 | Cross-tenant isolation | POST from tenant_B a endpoint tenant_A clinic data | endpoint retorna 404 (cross-tenant bloqueado) | AC-5 (tenant scoped) |
| 4 | RBAC read-only | No-admin role abre Datos | campos visibles pero no editables + 403 intento POST | AC-4 (RBAC) |
| 5 | Preferencias timezone change | Admin cambia timezone | SELECT change + autosave + persist TenantLocale + fecha timestamp refleja zona | AC-2 (persist) |
| 6 | Preferencias moneda change | Admin cambia moneda a USD | SELECT change + autosave + persist + UI montos reflejan símbolo USD | AC-2 (persist) |
| 7 | Idioma read-only | Intenta editar idioma | campo read-only + badge "se deriva del país" | AC-4 (read-only correcto) |
| 8 | País read-only | Intenta editar país | campo read-only + badge "definido en el alta" | AC-4 (read-only correcto) |
| 9 | Tipo clínica read-only | Intenta editar tipo clínica | visualiza badge "definido en el alta" + no editable | AC-4 (read-only correcto) |
| 10 | DPO referencia | Abre "Responsable de datos" | VISTO DPO actual + link a /config/seguridad + NO formulario edición | AC-1 (datos reales) |
| 11 | Load real data | Abre "Mi cuenta" | VISTO datos del tenant actual (no placeholder, valores reales BD) | AC-1 (datos reales) |
| 12 | Live-verify write + effect | Admin escribe CUIT válido + autosave | POST 200 + DB clinic.fiscal_id actualizado + live-verify observa nuevo valor al recargar + audit_log row creado | AC-6 (live-verify) |

## § Criterios de aceptación (finales · post-D3-revoke)

- **AC-1** Sub-tab "Mi cuenta" renderiza datos reales del tenant (no placeholder `CuentaPlaceholder.tsx`).
- **AC-2** Editar campo editable + autosave persiste cambio en DB + sobrevive F5.
- **AC-3** Validación fiscal country-specific funciona: válido → persiste; inválido → error inline + NO persiste.
- **AC-4** Read-only correcto: tipo de clínica/país/idioma NO editables + rol no-admin VE read-only + 403 intento POST.
- **AC-4b** Especialidades AHORA EDITABLES (multi-select o chips removibles) + validación contra specialty_catalog del país + autosave.
- **AC-5** Datos tenant-scoped (cross-tenant request → 404; dual filter `tenant_id+clinic_id`).
- **AC-6** Live-verify REAL en dev-app: admin edita especialidades válidas + observa persist + audit_log row visible en logs.

## § Microcopy final

| Campo | Label | Hint | Badge |
|---|---|---|---|
| Nombre comercial | "Nombre comercial" | — | — |
| Razón social | "Razón social" | — | — |
| Tipo clínica | "Tipo de clínica" | "El tipo de clínica se definió al crear la cuenta. Para cambiarlo, escribe a soporte (afecta agentes, catálogo y compliance)." | "definido en el alta" |
| Especialidades | "Especialidades" | "Selecciona las especialidades que ofrece tu clínica. Se valida contra el catálogo del país. Cambios afectan ofertas de agentes." | — |
| País | "País" | "El país se definió al crear la cuenta. El cambio debe solicitarse a soporte." | "definido en el alta" |
| ID fiscal | "CUIT" / "RUC" / "RFC" / etc | "Formato {PAÍS} · se valida al guardar" | — |
| Dirección | "Dirección" | "Ej: Av. Corrientes 1234, C1043 CABA" | — |
| Teléfono | "Teléfono" | "Incluir código de país (ej. +54 11 4123-4567)" | — |
| Email | "Email de contacto" | "Para contactos de soporte y facturación" | — |
| Timezone | "Zona horaria" | — | — |
| Moneda | "Moneda" | "Se usa para mostrar montos en toda la plataforma" | — |
| Idioma | "Idioma" | "Se deriva del país de la clínica. Si necesitas otro, escribe a soporte." | "se deriva del país" |
| DPO | "Responsable de datos" | "Se configura en Seguridad y cumplimiento" | — |

## § Deliverables exactos

### Backend (no producir — CONSUME existente)
- ✓ `core/luana-core-tenant-profile` (tenant perfil + catalogs)
- ✓ `core/luana-core-iam` (iam + roles)
- ✓ `vitalia/modules/vitalia/fiscal/` (validators)
- ✓ `vitalia/modules/vitalia/clinics/` (clinic entity)
- ✓ `TenantLocale` (master-data timezone/currency)

### Frontend (nueva)
- `vitalia/frontend/src/app/[tenantId]/(shell-organism)/config/cuenta/page.tsx` — Server Component raíz
- `vitalia/frontend/src/app/[tenantId]/(shell-organism)/config/cuenta/layout.tsx` — layout N3-static SubSubTabsBar
- `vitalia/frontend/src/features/config/components/cuenta/AccountDataView.tsx` — `"use client"` + RHF + Zod
- `vitalia/frontend/src/features/config/components/cuenta/PreferencesView.tsx` — `"use client"` + TenantLocale `Select`
- `vitalia/frontend/src/features/config/components/cuenta/ResponsibleView.tsx` — read-only + link
- `vitalia/frontend/src/features/config/hooks/use-account-form.ts` — RHF + autosave hook
- `vitalia/frontend/src/features/config/types/cuenta-schema.ts` — Zod schema fiscal validators
- `vitalia/frontend/src/features/config/api/patch-clinic.ts` — React Query mutation
- Playwright e2e: `vitalia/frontend/e2e/specs/config/cuenta.spec.ts` (live-verify real writes)
- Visual goldens: `vitalia/frontend/e2e/goldens/cuenta-datos.png`, `cuenta-prefs.png`, `cuenta-resp.png` (3 sub-sub-tabs)

### Testing
- Unit: Zod validators fiscal (AR/PE/MX/CL/CO/UY) — all valid + all invalid formats
- Integration: PATCH /clinic fiscal_id=valid → 200 + DB reflect + audit_log row
- E2E live-verify: write CUIT válido + POST 200 + reload → persisted + logs (at least 1 write real ejercida)
- Arch: `test_phi_dual_filter.py` (clinic repos heredan `PhiRepositoryBase`)

### Docs
- `vitalia/docs/product/stories/vitalia-fase2-config-cuenta/03-arch.md` (architecture ready package — `/architect` produce)
- `vitalia/docs/product/stories/vitalia-fase2-config-cuenta/04-validators.yaml` (test construction plan)
- `vitalia/docs/product/stories/vitalia-fase2-config-cuenta/05-guidelines.md` (code style vitalia)
- `vitalia/docs/product/stories/vitalia-fase2-config-cuenta/06-tickets.yaml` (ticket assignments)
- Mockup final: `vitalia/docs/product/stories/vitalia-fase2-config-cuenta/mockups/cuenta.html` (ratificado)

## § Validación RONDA 2 checklist (antes de handoff `/architect`)

- ✓ Spec ejecutable: Gherkin AI-resistant (happy + negative + edge + adversarial)
- ✓ Matriz cobertura: 12 bifurcaciones → scenarios → verificación real
- ✓ AC enumerados: 6 criterios finales
- ✓ Mockup final: ratificado visual (`ratified_visual_by_chris: true`)
- ✓ Microcopy final: labels + hints + badges
- ✓ Deliverables exactos: paths + artefactos concretos
- ✓ Interrogatorio cerrado: Q1-Q8 resueltas + Chris ratificó
- ✓ Prior art: engine consumido (no recreado); net-new acotado
