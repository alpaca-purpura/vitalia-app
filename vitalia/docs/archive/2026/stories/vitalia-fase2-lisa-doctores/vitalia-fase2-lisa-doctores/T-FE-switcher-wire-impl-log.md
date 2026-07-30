# T-FE-switcher-wire — Implementation Log

- **Ticket:** T-FE-switcher-wire (06-tickets.yaml delta_v3 · group D3A-switcher · surface frontend)
- **Builder:** builder-frontend (Fable 5 — mandato Chris `model_mandate_2026_06_12`)
- **Dep:** T-CORE-picker-slot SHIPPED (commit 51d1aa80) — `entityIdentitySlot` verificado en disco (`EntitySubNavBar.tsx` L139 + `EntityWorkspaceLayout.tsx` L56, forwarding verbatim).
- **Brief:** CONTEXT-BRIEF.md leído (Validator pass populated · Faithfulness `partial`, cero HIGH → proceed). Gaps §11 relevantes a ESTE ticket: ninguno directo (F-1 download = T-BE-bio-docs; cap `dev_preview` stale anotado — el código vive en `components/staff/`, no `components/doctores/`).

## § Plan (technical_design — ANTES de escribir código)

### D1 — Design-system-first (qué reutilizo)

| Pieza | Origen | Modo |
|---|---|---|
| `EntityPicker` (canon §2.4: search server-side debounced 200ms + cursor 20 + windowed + a11y combobox) | `core/@luana/ui-kit/src/EntityPicker.tsx` | CONSUMO as-is (forbidden_to_touch core) |
| `EntityWorkspaceLayout.entityIdentitySlot` → `EntitySubNavBar` slot (canon §6.3) | `core/@luana/ui-kit` (T-CORE shipped) | CONSUMO — paso el nodo, cero edición core |
| `fetchClient` + `useTenantId` + `useClinicId` | `@/lib/api/fetchClient`, `@/hooks/*` | CONSUMO (patrón `useStaffList`) |
| Cero átomo nuevo, cero clase Tailwind nueva, cero estilo a mano | — | el picker trae su propio styling canon |

Verificación headers (mandato ticket "verificá el patrón real"): el GET list `/clinics/doctors` NO exige `useStaffActorHeaders` — `useStaffList` (L140-173 staff.ts) manda solo `token + tenantId + clinicId` (la lista es masked; el actor header X-User-ID es requisito solo del GET detail / mutations — bug #5 comment). El searchFn replica ese patrón exacto.

### D2 — Mockup adherence (`doctores.html::doctoresN3Bar`, FIRMA 2)

- Chip estático de identidad → trigger del picker con avatar iniciales + nombre + `▾` (EntityPicker trigger = ese contrato).
- Popover: search "Buscar integrante…" (placeholder del mockup) + listbox + footer "Mostrando N de M".
- Inactivos ocultos: filtro server `active=true` (RN-D3A-2) — footer del mockup "inactivos ocultos" queda implícito en el dataset filtrado.
- ✓ activo: el core marca selected vía `aria-selected=true` + `font-medium` (ver § Mockup scope notes — glifo ✓ y subtítulo specialty no existen en el core as-is).

### D3 — Scope (SOLO scenarios SC-D3A-1..4 + deliverables)

- IN: searchFn adapter page↔cursor · wiring slot en `StaffWorkspaceShell` · `onPickDoctor` preserva hoja · vitest + e2e + POM.
- OUT (el mockup muestra más): 4ª hoja "Página" (T-FE-pagina-publica) · subtítulo specialty en opciones (core picker as-is no lo soporta) · glifo ✓ literal (core usa aria-selected/font-medium) · cualquier cambio a `features/adrian/**`, `components/ui/**`, `app/layout.tsx`, `core/@luana/ui-kit/**`.

### Diseño técnico

1. **`features/lisa/api/staff.ts`** (EXTEND — archivo existente, M8 extend-no-destroy):
   - `pickerCursorToPage(cursor)` — puro: cursor=stringified page; null/garbage/<1 → 1.
   - `mapDoctorsPageToPickerResult(res: PaginatedDoctors, page)` — puro: items `{id, name: displayName || firstName lastName}`, `nextCursor = page < ceil(total/pageSize) ? String(page+1) : null`, total passthrough. Pure = unit-testeable sin mock de red.
   - `useDoctorPickerSearchFn(): EntitySearchFn` — hook `useCallback([getToken, tenantId, clinicId])` → **identidad estable** (el effect de fetch del EntityPicker depende de `searchFn`; identidad inestable = re-fetch loop con el popover abierto — runtime-quality-checklist § useEffect deps). Params: `page`, `page_size=limit`, `active=true` (RN-D3A-2), `q` si no vacío (RN-D3A-1 server-side). `API_BASE=""` relativo (patrón post bug#2).
2. **`StaffWorkspaceShell.tsx`** (EXTEND):
   - `buildDoctorWorkspaceHref(tenantId, doctorId, pathname)` — puro, exportado: deriva hoja actual de pathname (segmento 5 ∈ {perfil, horarios, servicios, pagina}; fallback `perfil`) → `/{tenantId}/lisa/staff/{doctorId}/{leaf}`. "pagina" ya está en el set válido para que el leaf-preserve funcione cuando T-FE-pagina-publica agregue la 4ª hoja (cero acople: acá NO se agrega la leaf).
   - `onPickDoctor` — `useCallback`: same-id → no-op; else `router.push(buildDoctorWorkspaceHref(...))`.
   - Slot: `useMemo(() => entity ? <EntityPicker value={entity} searchFn onChange testId="doctor-picker" searchPlaceholder="Buscar integrante…"/> : undefined)` → `entityIdentitySlot` de `EntityWorkspaceLayout` (variable, no JSX inline-as-prop). Master/loading (entity=null) → slot undefined → core nunca lo renderiza (guard T-CORE).

### Batería de tests (test-design-doctrine: hook/adapter + component wiring + e2e ruta crítica)

RED primero:
1. `api/__tests__/staff-picker-adapter.test.ts` — puro: cursor↔page (null→1, "3"→3, garbage→1) · nextCursor en página intermedia/última · total · displayName fallback · pageSize 0 guard. + hook: searchFn manda `active=true` + `q` + `page_size` (mock fetchClient).
2. `components/staff/__tests__/staff-picker-wire.test.tsx` — `buildDoctorWorkspaceHref` (preserva horarios/servicios/pagina · fallback perfil · null pathname) + render `StaffWorkspaceShell`: slot reemplaza identidad estática (`entity-identity-slot` presente, `aria-label="Editando: …"` ausente) · abrir picker → opción → click → `router.push` con hoja PRESERVADA · mismo doctor → no push.
3. Regresión embudo (slot opt-in NO cambia EntitySubNavBar default): correr `features/adrian/.../LeadWorkspace.test.tsx` SIN tocarlo + tsc downstream.
4. e2e `regression/vitalia-fase2-lisa-doctores/staff-picker-switcher.spec.ts` — SC-D3A-1..4 vía `real-backend-forward.fixture` (auth Clerk + forwarding BE real + gate anti-burbuja base.ts — NUNCA `@playwright/test` directo, cero mock del surface). POM `DoctorWorkspacePage` EXTEND con locators del picker.

### Integración (CONN)

- **C**onsumed: el slot lo monta `StaffWorkspaceShell`, ya montado en TODA ruta `/{tenantId}/lisa/staff/[doctor-id]/*` (layout existente — cero ruta nueva). El searchFn consume el endpoint real existente (`GET /clinics/doctors` — 03-arch-delta §2.3: CERO cambio BE).
- **O**n-map: cap `lisa.doctores` (header `// cap: clinics.lisa.doctores` ya presente en ambos archivos editados; los archivos nuevos de test llevan el mismo header).
- **N**avigable: trigger visible en la franja N3 de cada hoja del workspace.
- **N**otarized: cableado vía prop del layout core (registro = el propio render path existente).

### Riesgos identificados pre-código

- Stale `searchFn` identity → loop de fetch (mitigado: useCallback deps mínimos estables).
- `value` del picker debe seguir al doctor activo tras navegar (entity deriva del query detail por `doctorId` del nuevo route → se actualiza solo).
- Virtualizer @tanstack/react-virtual bajo jsdom: copiar stubs ResizeObserver + offsetWidth/Height del test core (patrón documentado en `EntityPicker.test.tsx` L33-67).

## § Skills Consulted

(se completa al cierre — ver T-FE-switcher-wire-result.md § Skills Consulted, copia canónica)
