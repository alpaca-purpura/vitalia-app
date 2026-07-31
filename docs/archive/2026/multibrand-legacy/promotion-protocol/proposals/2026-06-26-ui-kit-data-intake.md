---
slug: 2026-06-26-ui-kit-data-intake
state: proposed                       # proposed | under_review | accepted | rejected | migrated
opened_date: 2026-06-26
opened_by: /pm-luana
ratified_by: null                     # Chris cuando ratifica APPROVED/REJECTED
ratified_date: null

kind: lift-new-component              # CREATE en el kit (ADR-016 §2) — lift de código REAL desde nicolify (≠ extend)
target_package: core/@luana/ui-kit
target_component: src/data-intake.tsx # archivo NUEVO (no existe intake en el kit hoy)
origin_story: nicolify/docs/product/stories/nicolify-r1-abel-icp-buyer
origin_component: nicolify/frontend/src/components/shared/intake/UniversalIntake.tsx  # renombra UniversalIntake → DataIntake

semver_impact: minor                  # componente nuevo opt-in, cero breaking · 0.9.0 → 0.10.0 (reconcile contra current al lift)
ds_action: CREATE                     # ADR-016 §2 — genérico-por-naturaleza, ≥3 consumidores ya existentes (nicolify live + vitalia/comunify one-offs)
ds_destino: kit
blocks: []                            # adopción vitalia/comunify = stories aparte (no bloquea)
related:
  - 2026-06-25-ui-kit-datepicker-atom # misma familia ui-kit, mismo programa core-ds-foundation
program: core-ds-foundation           # Fase C · DS · ADR-016
---

# Promotion proposal — `DataIntake` en `@luana/ui-kit` (mecanismo de ingesta de datos de la plataforma)

## Resumen

Nicolify construyó `UniversalIntake` (molécula de ingesta 4 modos: URL · Archivo · Texto · Conectar)
para el ICP de Abel. Chris pide **promoverlo a `@luana/ui-kit` como `DataIntake`** para que sea
idéntico en todas las marcas y, sobre todo, **el mecanismo de ingesta de datos de la plataforma**
(la mitad-FE de un mecanismo cuya mitad-BE ya es del engine: `core/luana-core-extraction/base_orchestrator.py`).

**Decisión de gobernanza (ADR-016 §2):** acción = `CREATE` (lift de código genuinamente genérico),
destino = `kit`. Es un *lift*, no una *adopción*: el núcleo (mode-switcher + url/file/text + file→base64
+ submit + tablist accesible) es genérico; lo que lo amarra a Abel/ICP se externaliza vía props/slots
(composición sobre configuración).

## Por qué cross-brand (evidencia dura)

La ingesta FE está **fragmentada** — cada marca reinventó su uploader/intake:

| Marca | Hoy | Razón |
|---|---|---|
| nicolify | `UniversalIntake` (live · ICP de Abel) | **origen** — 4 modos, ya en producción |
| vitalia | `components/ui/dropzone.tsx` + `features/vitalia/.../patient-medical-pdf-upload.tsx` | 4-5 one-offs de upload sin unificar |
| comunify | `features/comunify/.../voice-samples-uploader.tsx` | uploader propio |
| **BE (las 4)** | `core/luana-core-extraction/base_orchestrator.py` | **ya compartido** — el motor de extracción es del engine |

≥3 consumidores reales hoy → `CREATE` en el kit es el destino correcto (no `ADAPT`/brand-local).
Promover el componente **completa la mitad-FE** de un mecanismo cuya mitad-BE ya vive en `core/`.

## API (composición · ADR-016 §3: variant-props + slots + labels)

```ts
export type IntakeMode = "url" | "file" | "text" | "connect";

export interface IntakeSeed {            // payload GENÉRICO (no IcpExtractRequest)
  mode: "url" | "file" | "text";         // "connect" no emite seed (rutea a config)
  url?: string;
  text?: string;
  file?: { name: string; base64: string; size: number; mimeType: string };
}

export interface DataIntakeLabels {      // copy Spanish-neutro override por uso/i18n
  urlLabel: string; urlPlaceholder: string; urlHint?: string;
  fileLabel: string; fileHint?: string;
  textLabel: string; textPlaceholder: string; textHint?: string;
  connectLabel: string;
  submitLabel: string; submittingLabel: string; cancelLabel: string;
  fileTooBigError: string;               // {max} interpolado
}

export interface DataIntakeProps {
  onSubmit: (seed: IntakeSeed) => void;  // consumer mapea seed → su API de ingesta
  onCancel?: () => void;                 // si ausente → no renderiza botón Cancelar
  modes?: IntakeMode[];                  // default ["url","file","text"]; +"connect" opcional
  initialMode?: IntakeMode;
  accentSlug?: string;                   // color de agente · default --primary (ver Nota G3 abajo)
  isSubmitting?: boolean;
  fileAccept?: string;                   // default broad (".pdf,.doc,.docx,.csv,.txt")
  maxSizeMB?: number;                    // default 10 · VALIDA + error (net-new, ver abajo)
  labels?: Partial<DataIntakeLabels>;
  renderConnect?: () => React.ReactNode; // slot para el CTA "conectar fuente" de la marca
  className?: string;
}
```

### Tabla de extensión (origin → kit)

| Acople a Abel/ICP (origin) | Generalización (kit) |
|---|---|
| `bg/text-agent-abel` ×4 (hex Abel hardcodeado) | prop `accentSlug` → CSS var, default `--primary` |
| Copy "Abel analizará…/Describe tu cliente ideal/Analizar" | `labels` object (Spanish-neutro defaults) |
| Emite `IcpExtractRequest` (con `icpId`) | emite `IntakeSeed` genérico; consumer mapea |
| `SeedType`/`IntakeMode` en `features/abel` (español) | tipos en `@luana/ui-kit` (inglés, convención del kit) |
| 4 modos fijos | prop `modes[]` (elegir/ordenar/habilitar) |
| `.pdf,.doc…` + "10 MB" solo como copy | props `fileAccept` + `maxSizeMB` (**+ validación real**) |
| `tenantId` prop → `<Link>` interno a `/{tenant}/config/conexiones` | slot `renderConnect` (consumer dueño del Link + tenant) |
| imports `@/components/ui/*`, `@/lib/utils` | `@luana/ui-kit` + `@luana/format/utils` |

## Análisis técnico — la API cierra, con 3 ajustes (todos reales)

La API propuesta por Chris **cierra**. Tres sharpenings, ninguno especulativo:

1. **`maxSizeMB` es NET-NEW behavior, no solo prop.** El origin muestra "PDF, Word, CSV — hasta 10 MB"
   como copy en un `<span>` pero **no valida nada** (el origin miente). El lift debe agregar el chequeo
   real (`file.size > maxSizeMB*1024*1024` → error state, no submit) + test. Es la única conducta nueva
   del lift.
2. **`accentSlug` NO puede ser `bg-agent-${slug}`** — Tailwind JIT purga clases por template-literal
   (regla G3 JIT-safe). Mecanismo correcto: el slug resuelve a una **CSS var** que el `<style>` del
   componente consume — `style={{ "--intake-accent": \`var(--agent-${accentSlug})\` }}` (CSS vars no se
   purgan; el `var(--agent-abel)` lo provee el theme de la marca). Default `--primary`. La marca define
   `--agent-{slug}` en su theme (patrón color-por-agente, canon §2.8).
3. **`IntakeSeed.file` más rico que el origin** (`{name,base64,size,mimeType}` vs `fileContent/fileName`
   flat) — mejora correcta: habilita el chequeo de tamaño + da mimeType al BE. El wrapper de nicolify
   mapea `seed.file.base64 → fileContent`, `seed.file.name → fileName`.

Detalles menores ya correctos en la API: `onCancel` opcional (sin él, sin botón), `renderConnect` slot
elimina el acople a `tenantId`/routing, `IntakeSeed.mode` excluye `"connect"` a propósito (no emite seed).

### Riesgo

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Otra marca consume y descubre límite del contract | Baja | API por slots/labels/props ya cubre los 3 acoples conocidos |
| Bump minor + marca no opt-in | Nula | componente nuevo, cero call-site existente |
| `accentSlug` mal cableado (Tailwind concat) rompe color | Media | Nota G3 arriba — CSS var, gate eslint no-arbitrary + render-smoke |

## Queda brand-local (NO se promueve — es dominio)

`IcpIntakeOverlay` (Dialog + estados analizando/error + poll del extract-job), `DraftFirstStarter`
(empty-state ICP), `useIcpExtract`, y el mapeo `IntakeSeed → IcpExtractRequest`. Eso es dominio de Abel
(`KEEP` brand-local). **Límite de scope:** `DataIntake` = ingesta de DATOS para procesar (url/file/text
→ extracción). NO absorbe `AvatarUploader`/crop de imagen (asset visual, otro concern).

## Plan de ejecución (accepted → migrated)

1. **Build kit:** `core/@luana/ui-kit/src/data-intake.tsx` — `DataIntake` + `IntakeMode`/`IntakeSeed`/`DataIntakeLabels`
   exports en `index.ts`. Portar el tablist accesible (roving tabindex) **verbatim** del origin (ya es sólido).
   Agregar la validación `maxSizeMB` (net-new) + accent vía CSS var (Nota G3). Labels Spanish-neutro default.
2. **Story Storybook** (`Molecules/DataIntake`): estados `url` · `file` · `text` · `connect` (slot) ·
   `submitting` · `error file-too-big`. (SSoT visual — ADR-016 §5.)
3. **Verificación LIVE Chrome** (Storybook :6007): los 3 modos + drag/drop file + slot connect + el error
   file-too-big. **Gates:** `tsc --noEmit` 0 · render-smoke (`scripts/_smoke_storybook.mjs`) · vitest
   (≥ test del size-validation + cada modo emite el `IntakeSeed` correcto).
4. **Refactor nicolify:** `UniversalIntake.tsx` → wrapper fino que importa `DataIntake` de `@luana/ui-kit`,
   mapea `IntakeSeed → IcpExtractRequest`, pasa `accentSlug="abel"` + labels ICP + `renderConnect`. Borrar el
   código duplicado del mirror. `tsc` nicolify verde.
5. **Bump** `0.9.0 → 0.10.0` (reconcile contra current al lift) + CHANGELOG. Commit platform-only.
6. **`state → migrated`** + summary.
7. **Adopción vitalia/comunify** = stories aparte por marca (handoff `/pm-{brand}`) — reemplazan sus
   one-offs (`dropzone`, `patient-medical-pdf-upload`, `voice-samples-uploader`) por `DataIntake`. NO bloquea.

## Decisión

**Recomendación `/pm-luana`:** **APPROVED** — patrón genuinamente transversal (≥3 consumidores hoy + mitad-BE
ya en engine), API por composición sin leakage de dominio, semver minor opt-in (cero riesgo downstream),
los 3 ajustes son operacionalización, no objeciones. ADR-016 `CREATE`/`kit` correcto.

**Ratificación Chris:** _(pending — pasa a accepted al APPROVED)_

## Bitácora

- 2026-06-26: opened by /pm-luana (mandato directo Chris, contexto completo provisto) — state `proposed`.

## Cross-references

- Origin: `nicolify/frontend/src/components/shared/intake/UniversalIntake.tsx` (+ `IcpIntakeOverlay`, `use-icp-extract`, `extract.ts`)
- BE compartido: `core/luana-core-extraction/base_orchestrator.py`
- Doctrina: `docs/architecture/luana-platform/ADR-016-design-system-inventory-governance.md` (§2 árbol reuse/extend/create · §3 toolkit · §5 contrato por actor)
- Programa: `docs/product/stories/core-ds-foundation/checkpoint.md` (Fase C · DS)
- Hermana: `docs/promotion-protocol/proposals/2026-06-25-ui-kit-datepicker-atom.md`
- Reglas: `.claude/rules/frontend-visual-fidelity.md` (G3 JIT-safe · canon §2.8 color-por-agente)
