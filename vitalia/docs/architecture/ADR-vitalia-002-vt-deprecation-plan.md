<!-- voseo-allowed: internal architecture documentation -->

---
brand: vitalia
adr_id: ADR-vitalia-002
title: "Plan de deprecación progresiva de clases .vt-* hacia Tailwind estándar + Shadcn"
status: accepted
date: 2026-05-23
authors: [/architect, /pm-vitalia]
supersedes: null
links:
  spec: "docs/product/stories/vitalia-fase1-stack-stability/01-spec.md"
  arch: "docs/product/stories/vitalia-fase1-stack-stability/03-arch.md"
  arch_test: "vitalia/frontend/src/__tests__/architecture/test-no-vt-classes-in-new-features.test.ts"
  design_contract: "vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md"
---

# ADR-vitalia-002 — Plan de deprecación progresiva de clases .vt-\*

## § 1 — Contexto

### Por qué existen las clases `.vt-*`

Vitalia inició su frontend con un sistema de tokens propietario basado en variables CSS `--vitalia-*` consumidas via clases de utilidad custom `.vt-bg-*`, `.vt-text-*`, `.vt-border-*`. Este enfoque fue pragmático en el bootstrap inicial: centraliza colores en un solo lugar (`globals.css`), evita valores HSL en TSX, y permite refactors globales con búsqueda simple.

Ejemplo:
```css
.vt-bg-cian { background-color: hsl(var(--vitalia-cian)); }
.vt-text-muted { color: hsl(var(--vitalia-text-muted)); }
.vt-border { border-color: hsl(var(--vitalia-border)); }
```

Actualmente existen ~150+ clases `.vt-*` en `globals.css` consumidas por:
- `src/app/[tenantId]/(dashboard)/` — páginas dashboard shipped
- `src/features/analytics/` — componentes Growth Studio
- `src/features/marketing/` — página landing/marketing

### El problema: deuda técnica con Shadcn UI

La Fase 1 del shell agéntico introduce Shadcn UI como el sistema de componentes canónico. Shadcn utiliza clases Tailwind directas (`bg-background`, `text-foreground`, `bg-primary`, etc.) consumiendo variables CSS estándar (`--background`, `--foreground`, `--primary`, etc.).

Las `.vt-*` generan los siguientes problemas:

1. **Colisión semántica**: `--vitalia-muted` ≠ `--muted` (distintos valores HSL). Los componentes Shadcn no pueden consumir `.vt-*`.
2. **Doble sistema de colores**: dos namespaces paralelos (`vitalia-cian` + `primary`) para conceptos que deberían mapear 1:1.
3. **Tooling friction**: Tailwind IntelliSense, prettier-plugin-tailwindcss, y class-variance-authority no reconocen `.vt-*`.
4. **No hay dark mode**: el sistema `.vt-*` fue diseñado antes de dark mode. Agregar `.dark` requiere duplicar ~150 clases.
5. **Migración shell incompleta**: los componentes del shell agéntico (F1-S2 a F1-S10) deben usar Tailwind estándar para que Shadcn primitives se integren sin fricción.

### Alineación con el Design Contract

El `SHELL-DESIGN-CONTRACT.md` (ratificado Chris 2026-05-22) cementa:
- D2: "Deprecar `.vt-*` COMPLETO en el shell agéntico"
- D3: "Migration path = route group paralelo (coexistencia temporal)"
- D5: "7 agent tokens (`--agent-*`) usando CSS vars Shadcn-compatible"

---

## § 2 — Inventario `.vt-*`

Scan de `src/app/globals.css` al 2026-05-23:

### Backgrounds (13 clases)
```
.vt-bg-app, .vt-bg-surface, .vt-bg-surface-alt, .vt-bg-muted,
.vt-bg-cian, .vt-bg-cian-10, .vt-bg-cian-8,
.vt-bg-azul-marino, .vt-bg-danger-12, .vt-bg-warning-12,
.vt-bg-success-12, .vt-bg-success, .vt-bg-success-soft, .vt-bg-danger-soft
```

### Text colors (9 clases)
```
.vt-text, .vt-text-muted, .vt-text-faint, .vt-text-cian,
.vt-text-azul-marino, .vt-text-danger, .vt-text-warning,
.vt-text-success, .vt-text-white
```

### Borders (9 clases)
```
.vt-border, .vt-border-soft, .vt-border-cian, .vt-border-cian-l,
.vt-border-verde-lima, .vt-border-danger-30, .vt-border-warning-30,
.vt-border-success-30, .vt-border-danger-soft
```

### Ring / Divide / Gradient (8 clases)
```
.vt-ring-cian, .vt-divide-border-soft,
.vt-bg-gradient-agent, .vt-bg-gradient-app-cta, .vt-bg-gradient-mariposa,
.vt-bg-tab-active, .vt-border-b-cian, .vt-text-azul-marino-bold
```

### Agent gradients (3 clases)
```
.vitalia-agent-gradient-valeria, .vitalia-agent-gradient-adrian, .vitalia-agent-gradient-lucas
```

**Total: ~42 clases utilitarias custom** (más las variantes inline en el CSS). Consumidores principales en `(dashboard)/` y `features/analytics/`.

---

## § 3 — Estrategia de compatibilidad temporal

### Principio de coexistencia

En F1-S0, las `.vt-*` **NO se eliminan ni modifican**. Coexisten con el nuevo sistema Shadcn. Esto garantiza que el `(dashboard)/` shipped no regrese visualmente.

### ¿Por qué NO migrar ahora?

1. **Scope F1-S0**: F1-S0 es infra bootstrap (Shadcn install + tokens). Migrar 150+ clases en componentes shipped está fuera del scope y podría introducir regresiones visuales.
2. **Route group paralelo**: el shell agéntico vive en `(shell-organism)/`, separado de `(dashboard)/`. Son dos route groups paralelos que pueden coexistir temporalmente.
3. **Golden regression**: los goldens Playwright del `(dashboard)/` detectan cualquier cambio visual. Migrar sin goldens actualizados = build break.

### Mapping de compatibilidad (para futuro uso)

Durante la migración progresiva (F2 stories), las `.vt-*` mapearán a Tailwind directo:

| Clase `.vt-*` actual | Tailwind directo equivalente |
|---|---|
| `.vt-bg-app` | `bg-background` |
| `.vt-bg-surface` | `bg-card` |
| `.vt-bg-muted` | `bg-muted` |
| `.vt-text` | `text-foreground` |
| `.vt-text-muted` | `text-muted-foreground` |
| `.vt-text-faint` | `text-muted-foreground/60` |
| `.vt-text-cian` | `text-primary` |
| `.vt-border` | `border-border` |
| `.vt-bg-cian` | `bg-primary` |
| `.vt-bg-cian-10` | `bg-primary/10` |
| `.vt-bg-danger-12` | `bg-destructive/12` |
| `.vt-text-danger` | `text-destructive` |
| `.vt-border-danger-30` | `border-destructive/30` |

---

## § 4 — Migration policy progresiva

### Regla forward-only

**Regla:** Todo código nuevo en `(shell-organism)/` y `components/shared/shell-organism/` DEBE usar Tailwind estándar + semantic tokens (`bg-background`, `text-foreground`, `bg-agent-lisa`, etc.). Las `.vt-*` están prohibidas en código nuevo.

Esta regla está enforced por el arch fitness test `test-no-vt-classes-in-new-features.test.ts` (T-5).

### Proceso de migración por story

Para cada feature story Fase 2 que modifique componentes legacy:

1. **Inventariar**: listar todas las `.vt-*` usadas en el componente
2. **Mapear**: usar tabla § 3 (o derivar equivalente Tailwind)
3. **Migrar inline**: reemplazar en el componente
4. **Actualizar goldens**: si el cambio es visual, actualizar snapshots Playwright y obtener ratificación Chris
5. **No eliminar del CSS aún**: la clase CSS legacy permanece en `globals.css` hasta que 0 consumidores la usen

### Tracking de consumidores

Antes de eliminar una clase `.vt-*` de `globals.css`:

```bash
grep -rn "vt-<nombre-clase>" vitalia/frontend/src/ --include="*.tsx" --include="*.ts" --include="*.css"
# Output debe ser 0 resultados antes de eliminar
```

---

## § 5 — Final drop

### Story dedicada al cierre Fase 2

Al completar todas las stories Fase 2 que migran componentes:

1. **Story**: `vitalia-fase2-vt-deprecation-final`
2. **Tarea**: eliminar bloque `.vt-*` completo de `globals.css`
3. **Prerequisito**: 0 consumidores de `.vt-*` en `src/` (verificado por grep)
4. **Gate**: goldens regression clean (todos los `(dashboard)/` goldens pasan sin diff)
5. **Arch test**: `test-no-vt-classes-in-new-features.test.ts` expandido para cubrir `src/` completo (no solo `shell-organism/`)

### Decisión diferida: ¿eliminar también `--vitalia-*` vars?

Las variables CSS `--vitalia-*` en `:root` son separables de las clases `.vt-*`. Podrían mantenerse como aliases para custom CSS (gradients, etc.) incluso después del drop de clases. Esta decisión se toma en `vitalia-fase2-vt-deprecation-final` con inventario real de consumidores.

---

## § 6 — Arch fitness test enforcement

### Ratchet test

**Archivo**: `vitalia/frontend/src/__tests__/architecture/test-no-vt-classes-in-new-features.test.ts`

**Mecanismo**: walkFiles sobre `src/app/[tenantId]/(shell-organism)` y `src/components/shared/shell-organism`. Para cada `.tsx?|.css`, verifica ausencia del patrón `/\bvt-[a-z]/`.

**GREEN por vacuidad inicial**: los paths no existen en F1-S0. El test pasa via iteración vacía. Cuando F1-S4 crea `(shell-organism)/`, el test empieza a escanear — cualquier `.vt-*` en ese código nuevo es un fail.

**Ratchet shrink-only**: una vez que la regla existe, no se puede relajar sin justificación en el commit. El allowlist es vacío por design (la regla no tiene excepciones para código nuevo).

### ESLint complementario (future)

En `vitalia-fase2-vt-deprecation-final`, agregar regla ESLint custom o plugin para detectar `.vt-*` en className strings — cubre casos donde el arch test de FS podría no alcanzar (templates dinámicos, cva variants, etc.).

---

## § 7 — Post-install audit checklist supply-chain

### Objetivo

Prevenir código malicioso inyectado en los primitivos Shadcn instalados. Shadcn es un registry copy-paste, no un npm package — el código vive en el repo. Cualquier divergencia del registry oficial debe ser entendida y documentada.

### Checklist post-instalación (cada PR que agrega/actualiza primitivos)

**Para cada archivo en `src/components/ui/`:**

1. **Diff contra registry oficial**:
   ```bash
   # Descargar source oficial desde registry
   curl -s "https://ui.shadcn.com/r/styles/new-york/<primitive>.json" | jq -r '.files[0].content' > /tmp/<primitive>-official.tsx
   diff vitalia/frontend/src/components/ui/<primitive>.tsx /tmp/<primitive>-official.tsx
   ```

2. **Verificar ausencia de**:
   - `fetch()` / `XMLHttpRequest` / `eval()` / `Function()`
   - Importaciones de dominios externos (solo `@radix-ui/*`, `lucide-react`, `class-variance-authority`, `clsx`, `tailwind-merge`)
   - `dangerouslySetInnerHTML`
   - Comentarios ofuscados (base64, unicode escapes)

3. **Lockfile review** (pnpm-lock.yaml):
   - Cada `@radix-ui/*` package tiene `resolved:` URL apuntando a `registry.npmjs.org`
   - Integrity hashes presentes (`integrity: sha512-...`)
   - Sin packages de registries alternativos

4. **Version pinning**:
   - `clsx@^2.x`, `tailwind-merge@^3.x`, `class-variance-authority@^0.7.x` — rangos MINOR permitidos
   - No `*` ni ranges amplios en `@radix-ui/*`

### Primitivos auditados en F1-S0

| Primitivo | Importaciones externas | `dangerouslySetInnerHTML` | `eval()` | Diff oficial |
|---|---|---|---|---|
| button.tsx | @radix-ui/react-slot, class-variance-authority, @/lib/utils | NO | NO | Minimal (no inline style, data-slot attrs) |
| avatar.tsx | @radix-ui/react-avatar, @/lib/utils | NO | NO | Clean |
| dropdown-menu.tsx | @radix-ui/react-dropdown-menu, lucide-react, @/lib/utils | NO | NO | Clean |
| input.tsx | @/lib/utils | NO | NO | Clean |
| badge.tsx | @radix-ui/react-slot, class-variance-authority, @/lib/utils | NO | NO | Clean |
| textarea.tsx | @/lib/utils | NO | NO | Clean |
| tabs.tsx | @radix-ui/react-tabs, @/lib/utils | NO | NO | Clean |
| tooltip.tsx | @radix-ui/react-tooltip, @/lib/utils | NO | NO | Clean |

**Veredicto F1-S0**: 8 primitivos CLEAN. Sin inyección detectada. Auditor-frontend revisa diff como parte del PR review.

---

## § 8 — Riesgos + mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| **Tailwind v4 incompatible con React 19** | Baja (Tailwind v4 stable Q1 2026 per upstream) | Alto (build break) | Fallback: downgrade Tailwind v3 temporario + pin `tailwind@3.x` hasta v4 stabilize. F1-S0 T-7 verifica empíricamente (`npm run build` + goldens). |
| **Shadcn React 19 peer-dep conflict** | Baja (Shadcn declaró React 19 compat 2025-Q4) | Medio (install warnings, posibles runtime crashes) | Workaround: `package.json` `overrides: { "react": "$react" }`. Fallback: pin Shadcn CLI a release verificado con React 19. |
| **`.vt-*` deprecation rompe (dashboard) shipped** | Media (si se migra prematuramente) | Alto (regresión visual usuario) | Regla F1-S0: NO migrar `.vt-*` en F1-S0. Goldens regression captura cualquier cambio visual en `(dashboard)/`. |
| **Registry supply-chain (npm @radix-ui)** | Muy baja (paquetes maduros, alta reputación) | Crítico (código malicioso en producción) | Checklist § 7: diff vs oficial, integrity hashes en lockfile, no rangos `*`. Auditor-frontend revisa en PR. |
| **CSS vars colisión (`--muted` shadcn vs `--vitalia-muted` legacy)** | Ya mitigado (nombres distintos) | Bajo (overrides inesperados) | Los nuevos vars usan nombres sin prefijo (`--muted`); los legacy usan `--vitalia-muted`. No hay colisión. |
| **Playwright goldens flaky en CI** | Media (animations, fonts, GPU rendering variance) | Medio (false positives) | `animations: 'disabled'`, `caret: 'hide'`, `maxDiffPixelRatio: 0.001`. Fuentes: Google Fonts cacheadas en CI. |
| **Goldens commit weight** | Baja (6 goldens × ~50-200KB) | Bajo (repo crece) | Goldens en `e2e/__screenshots__/` gitignored en `.gitignore` (solo se commitean en PR T-4 explícito). |
| **`@radix-ui` peer-dep warnings con React 19** | Alta (visx también tiene warnings) | Bajo (warnings no errores) | Pre-existing en el repo. Monitorear en node_modules pero no bloquean build/tests. |

---

## Decisiones registradas

| # | Decisión | Rationale |
|---|---|---|
| D1 | NO migrar `.vt-*` en F1-S0 | Scope F1-S0 = infra bootstrap, no migración |
| D2 | Arch test `test-no-vt-classes-in-new-features` GREEN by emptiness | TDD-first: test precede código nuevo |
| D3 | `@layer base` en globals.css (no nuevo archivo) | Shadcn canonical pattern, menos archivos |
| D4 | Coexistencia `--vitalia-*` + `--background/--primary` | Nombres distintos, 0 colisión |
| D5 | `--agent-*` tokens = CSS vars estilo Shadcn (H S% L%) | Consistencia con primitivos Shadcn |
| D6 | Final drop en story dedicada `vitalia-fase2-vt-deprecation-final` | Scope controlado, no en Fase 1 |
