---
story_id: vitalia-fase2-lisa-servicios
surface: frontend
owner: builder-frontend
auditor: auditor-frontend
parent: 03-arch.md
---

# 03-arch-fe — `features/lisa/components/servicios/` (FSD-Lite · ADR-vitalia-004) · Sub-phase A

> COMPOSE del canon `@luana/ui-kit` 0.4.1 (`design-system-canon.md` §2). ❌ `<select>` nativo · ❌ arbitrary values · ❌ Shadcn Tabs internas. `tenant_id` de `useTenantId()` (NUNCA `orgId`).
> Cada componente NEW → mockup'eado (`mockups/`) → build fiel en Next.

## 1. Routing (ADR-004 §3.1 + §3.1.1)

```
app/[tenantId]/(shell-organism)/lisa/servicios/
├── page.tsx                    # Server Component → redirect /lisa/servicios/catalogo (N3 default)
├── [subsubtab]/page.tsx        # subsubtab ∈ catalogo|escalera → LisaServiciosView initialView
├── [offer-id]/
│   ├── layout.tsx              # Server → EntityWorkspaceLayout (skeleton store-free G2)
│   └── [leaf]/page.tsx         # leaf ∈ resumen|para-adrian|especialistas|plan-pago|prueba-social
└── nuevo/page.tsx              # picker biblioteca inline → crea borrador → router.replace([offer-id])
```
- Server Components default. `getServiciosInitialState({tenantId, view})` + `getServicioWorkspaceState({tenantId, offerId, leaf})` SSR (cookies forwarded).
- `params`/`searchParams` async (Next.js 16 Promise). PHI nunca en URL (offer-id = UUID no-PHI).
- **`shell-routes.ts` EDIT (SSoT · arch test):**
  ```ts
  AGENT_SUBSUBTABS["lisa.servicios"] = [
    { id: "catalogo", label: "Catálogo", icon: "📋" },
    { id: "escalera", label: "Escalera", icon: "🪜" },
  ];
  // N3_DEFAULT_LEAF += [new RegExp(`^/(${UUID_SEG})/lisa/servicios/?$`,"i"), "catalogo"]
  ```

## 2. Client root (ADR-004 §3.3)
- `LisaServiciosView.tsx` (`"use client"` línea 1) — recibe `initialData` + `initialView`, hidrata React Query. Compone `ServiciosDirectoryHeader` + (`CatalogoView` | `EscaleraView`) según subsubtab.
- `ServicioWorkspaceView.tsx` — root del workspace `[offer-id]`. Compone `ServiceStatusBar` + `EntityWorkspaceLayout` (5 leaves). **Crear = editar (RN-16):** mismo componente, diferencias = campos vacíos/✨, chip Borrador, completitud baja.

## 3. Data layer (ADR-004 §3.4)
- **React Query keys** (convención `[module, subtab, action, ...filters]`):
  - `["offer","servicios","list",{search,category,active,origin}]`
  - `["offer","servicios","detail",offerId]`
  - `["offer","biblioteca","search",q]`
  - `["offer","servicios","specialists",offerId]`
  - `["offer","servicios","cases",offerId]` · `["offer","servicios","testimonials",offerId]`
  - Mutations (`useCreateFromTemplate`, `useCreateCustom`, `usePatchService`, `useToggleActive`, `useLinkSpecialist`, `useAddCase`, `useAddTestimonial`, `usePatchSalesBrief`, `useExtractDocument`) → `invalidateQueries` explícito.
- **Zustand UI-only** (`store/servicios-ui-store.ts`): filtros catálogo, picker open state, autosave dirty-flags per-field, escalera drag state. NO data fetched.
- **URL state:** subsubtab `catalogo|escalera` ES el SSoT del toggle (`?view=` legacy back-compat).

## 4. Forms + autosave (ADR-004 §3.5 + RN-20)
- `types/servicios-schema.ts` — Zod schemas. **Discriminated union por `modality`:**
  ```ts
  const modalitySchema = z.discriminatedUnion("modality", [
    z.object({ modality: z.literal("unica") }),
    z.object({ modality: z.literal("sesiones"), sessionsCount: z.number().int().min(1), interval: valueWithUnitSchema }),
    z.object({ modality: z.literal("recurrente"), cadence: valueWithUnitSchema }),
  ]);
  ```
  - `price: z.number().min(0)` (RN-11). Variants `{name, price>=0, note?}`. Numéricos tipados (RN-31 · min 1 sessions).
- **Autosave on-change debounce 600ms** (`use-autosave` canon §2.6) → PATCH por campo. **UNA** `FloatingAutosaveIndicator` (sticky abajo-centro, `role=status`). **Sin botón Guardar.** "Activar"/"Descartar borrador" = acciones de estado (no autosave). Toasts vía `sonner`.

## 5. Component map (cada § Inventario B → archivo · ui-kit primitive · mockup)

### Organismos (feature-local `features/lisa/components/servicios/`)
| Componente | Compone (ui-kit) | Mockup | Notas |
|---|---|---|---|
| `LisaServiciosView` | page-primitives + `SubSubTabsBar` (shipped) | catalogo/escalera.html | root; toggle N3-static |
| `ServiciosDirectoryHeader` | `Toolbar`+`FilterBar`+`Input`(search)+`Select`(filtros)+Button "+ Nuevo" | catalogo.html | RN-15 server-side search |
| `CatalogoView` | grid `EntityInfoCard` (Opción B) + `EmptyState` | catalogo.html | empty → invita biblioteca (AC-7) |
| `ServiceCard` (EntityInfoCard compose) | `EntityInfoCard`+`Badge`(`chip-origen`)+`Switch`(activo)+`Avatar`(specialists) | catalogo.html | sin badge peldaño (#8); kebab ⋮ |
| `EscaleraView` + `RungColumn` | `@dnd-kit/core` + `Card` + page-primitives | escalera.html | 5 fijos · layout full/3col/full · drag + keyboard a11y |
| `ServicioWorkspaceView` | `EntityWorkspaceLayout`+`EntitySubNavBar`(root-pill ‹ + `EntityPicker` ▾ + 5 leaves) | servicio-workspace.html | crear=editar (RN-16) |
| `ServiceStatusBar` | `Switch`(activo)+`Badge`(`chip-origen`)+`FichaCompletenessChip`+statuslink | servicio-workspace.html | header workspace; activo NUNCA bloqueado (AC-19) |
| `ResumenView` (leaf 1) | `Group`/`GroupHeader`+Input/Textarea/`RichSelect`/`ModalidadPicker`/`RungPicker`/`VariantsRepeater`/`NumberWithUnit` | servicio-workspace.html | 6 grupos: Identidad·Qué es·Procedimiento·Resultados·Riesgos·Modalidad-y-agenda |
| `ParaAdrianView` (leaf 2) | Textarea+`Switch`+`FaqPairList`+`ObjecionPairList`+`TagInput` | servicio-workspace.html | argumentario (AC-4.bis) |
| `EspecialistasView` (leaf 3) | list `EntityInfoCard`/row+`Avatar`+`EspecialistaLinkPicker` | servicio-workspace.html | vincular desde roster (no crea) |
| `PlanPagoView` (leaf 4) | `Group`+Input(number)+`Select`+`Switch`+derived read-only | servicio-workspace.html | 3 cobros (RN-6) + derivados Computed |
| `PruebaSocialView` (leaf 5) | grid `Case`(uploader+consent gate)+`TestimonialsList` | servicio-workspace.html | manual + consentimiento (RN-33) |
| `BibliotecaPicker` | page-primitives + `Input`(typeahead) + result list | nuevo-servicio.html | inline (NO modal · RN-16/25); "Usar plantilla"/"Crear personalizado" |
| `EspecialistaLinkPicker` | `Command`/checklist + `Input`(buscador) + `Avatar` | servicio-workspace.html | checklist roster · autosave al marcar (RN-20) |
| `KnowledgeSourcesPanel` | `Collapsible`(`<details>`) + dropzone + `Switch`(Adrián consulta) + `Badge`(estado) | servicio-workspace.html / nuevo-servicio.html | persistente+colapsable (RN-21); Procesar con Lisa (AC-11) |

### Moléculas NEW (feature-local)
| Componente | Contrato (props) | Compone | Mockup |
|---|---|---|---|
| `ModalidadPicker` | `value:'unica'\|'sesiones'\|'recurrente'`, `onChange`, `options:{value,title,desc}[]`, slot detalle revelado (progressive disclosure) | 3 cards + `NumberWithUnit`/`Select` revelados | `.modalidad-picker` |
| `RungPicker` | `value:ValueLevel`, `onChange`, `locked?:boolean` (estándar 🔒 RN-30), 5 opciones fijas | 5 botones | `.rung-picker` |
| `VariantsRepeater` | `value:{name,price,note}[]`, `onChange`(add/remove/edit), `currency` | `Input`+`NumberWithUnit`(price) rows | `.variants-list` |
| `TestimonialsList` | `value:{rating,text,author,source}[]`, `onChange` | rows + rating | `.testi-list` |
| `FaqPairList` / `ObjecionPairList` | `value:{q,a}[]` / `{type,response}[]`, `onChange` | par rows | markup pares |
| `TagInput` | `value:string[]`, `onChange`, chips + agregar | chips | (chips) |
| `FichaCompletenessChip` | `filled:number`, `total:number`, `missing:string[]`(tooltip) | `Badge`+`Tooltip` | `.completeness-chip` |

### Átomos NEW
| Componente | Dónde vive | Contrato | Mockup |
|---|---|---|---|
| **`NumberWithUnit`** | **`vitalia/frontend/src/components/shared/NumberWithUnit.tsx`** (vitalia-local shared · lift-candidate `/pm-luana`, NO lift esta story) | `value:number`, `onChange`, (`unit:string` **o** `units:string[]`+`unitValue`+`onUnitChange`), `min`/`step` | `.num-affix` |
| `chip-origen` | `features/lisa/components/servicios/` (o Badge variant) | `variant:'estandar'\|'personalizado'` | `.chip-origen` |

### CONSUME (NO recrear · ui-kit/shipped)
`RichSelect` (RN-32 "Tipo de cita inicial" · `options:{value,title,description}[]`) · `EntityWorkspaceLayout`/`EntitySubNavBar`/`EntityPicker`/`EntityInfoCard`/`Group`/`GroupHeader`/`FloatingAutosaveIndicator`/`Select`/page-primitives (`PageContainer`,`Toolbar`,`FilterBar`,`EmptyState`,skeletons) · `SubSubTabsBar` (shell-organism shipped) · `@dnd-kit/core` · Shadcn `Tooltip` (FieldTooltip RN-18 · subrayado punteado + ⓘ) · `Input`/`Textarea`/`Switch`/`Badge`/`Avatar`/`Card`/`Button`/`Collapsible`/`Command`.

## 6. Tooltips (RN-18 · texto literal del § Mapa de campos)
FieldTooltip (Shadcn Tooltip) en campos no obvios: peldaño, categoría, chip-origen, descripción (voz marca), variantes, riesgos (banner safety), modalidad, contraindicaciones, escalada, palabras clave, anticipo, reserva, moneda (read-only origen), derivados (read-only "se calcula solo"), completitud. Triviales (nombre) sin tooltip. Textos literales = § Mapa de campos del spec.

## 7. Escalera detail (AC-3)
- 5 peldaños FIJOS sobre `OfferValueLevel`: `lead_magnet`→"Gancho gratuito" · `activacion`→"Primera visita" · `transformacion`→"Tratamiento principal" · `maximizacion`→"Premium" · `corporativo`→"Plan/convenio".
- Layout: Gancho gratuito full-width arriba · {Primera visita · Tratamiento principal · Premium} 3 columnas medio · Plan/convenio full-width abajo.
- Drag (`@dnd-kit`) mueve `value_level` → autosave PATCH. **Estándar = peldaño locked** (RN-30 · drag aplica SOLO a personalizados). Keyboard a11y: Space(select)→Arrow(recorrer)→Space(soltar) + `aria-live` (AC-8). Peldaño vacío → guía qué va ahí + ejemplos de la biblioteca + "crear aquí".

## 8. Tests (TDD RED-first)
- Vitest: `RungPicker` (locked estándar), `ModalidadPicker` (discriminated reveal), `VariantsRepeater` (add/remove), `FichaCompletenessChip` (missing tooltip), `use-autosave` hook (debounce + UNA indicator), `useServiciosQuery`/mutations (MSW).
- Playwright funcional real-backend (auth fixture, NO mock del backend bajo prueba): crear-desde-plantilla (✨+canonical), crear-personalizado, typeahead sinónimo, autosave (sin botón), vincular-especialista (no crea), drag-escalera, keyboard-a11y escalera, consent gate caso, RBAC read-only, cross-tenant.
- Visual goldens (ADR-003 · maxDiffPixelRatio 0.001): `catalogo`, `escalera`, `servicio-workspace`, `nuevo-servicio` × light/dark = **8 PNGs** mapeados a los 4 mockups ratificados.
- axe a11y por screen state. Smoke spec ruta nueva `/lisa/servicios`.
- Live-verify (DoD #37 · chrome-devtools-verify): ejercer crear servicio + activar + autosave en dev-app real (write real + leer logs + confirmar persiste).

## 9. playwright_visual_scope
- **story_scope_routes:** `/{tenantId}/lisa/servicios`, `/{tenantId}/lisa/servicios/catalogo`, `/{tenantId}/lisa/servicios/escalera`, `/{tenantId}/lisa/servicios/[offer-id]/*`, `/{tenantId}/lisa/servicios/nuevo`.
- **forbidden_visual_changes:** `components/ui/**` (Shadcn primitives), `core/@luana/ui-kit/src/**` (lift-gate), `components/shared/shell-organism/**` (shell chrome shipped — solo CONSUME), otras features. EXCEPCIÓN permitida: crear `components/shared/NumberWithUnit.tsx` (NEW shared, no modifica existentes) + `shell-routes.ts` AGENT_SUBSUBTABS append (no modifica entries existentes).
- **non_egoismo:** no tocar scope de otras sesiones; commit por pathspec (`code:offer` FE+BE bucket).
