---
id: ADR-vitalia-001
title: Shared package vs. fork físico para componentes UI Slice 1
status: Accepted
date: 2026-05-18
deciders: [/architect, /pm-vitalia]
brand: vitalia
supersedes: []
references:
  - vitalia/docs/architecture/design-system.md
  - vitalia/docs/product/stories/vitalia-ux-discovery/03-arch-fe.md
  - .claude/rules/frontend-fsd.md
  - .claude/rules/anti-duplication.md
---

# ADR-vitalia-001 — Componentes UI Slice 1: fork físico vs. paquete compartido

## Contexto

Vitalia necesita implementar ~65 componentes de UI en Slice 1 que presentan
superposición funcional con componentes ya existentes en
`nicolify/frontend/src/features/{closer-studio,brand-studio,growth-studio,sales}/`.

La pregunta central: ¿copiamos los componentes a `vitalia/frontend/` adaptando
tokens (fork físico) o creamos un paquete compartido `@luana/ui-medical` consumido
por ambas brands?

## Criterios evaluados

### 1. Costo de mantenimiento vs. control de tokens

| Opción | Pro | Contra |
|---|---|---|
| **Fork físico** | Control total de tokens Vitalia sin afectar Nicolify. Cambios aislados por brand. Auditor puede revisar diff brand-scoped. | Duplicación code cross-brand (detectada por anti-duplication.md si patrón idéntico >50%). Actualizaciones upstream requieren merge manual. |
| **Paquete @luana/ui-medical** | DRY, una sola fuente para patrones comunes. Actualizaciones propagadas automáticamente. Promotion gate garantiza calidad. | Requiere promotion proposal a `/pm-luana` + arquitecto + semver. Overhead para 1 brand consumer. Vitalia tokens tendrían que ser externalizados via CSS vars o prop injection. |

**Decisión parcial:** el paquete compartido introduce overhead de governance
(promotion gate, semver, PR review cross-brand) que no está justificado cuando
Vitalia es la única brand con vertical médica. El fork físico reduce riesgo de
regresión cross-brand.

### 2. Velocidad de entrega vs. reutilización de código

Slice 1 tiene ~20 componentes NET NEW (vitalia-specific: `AgentAvatar`,
`PiiMaskedSpan`, `RequireRole`, `AuditedSection`, `DepositBadge`,
`ActivityStreamSticky`, `NPSTagBadge`, etc.) y ~45 que son adapters de
Nicolify con token reemplazo.

El trabajo de adaptación de tokens (reemplazar `purple-600` → `vitalia-azul-marino`,
`slate-100` → `vitalia-muted`) es mecánico y toma ~10-20 líneas por componente.
No requiere refactor estructural.

**Decisión parcial:** la velocidad de Slice 1 se maximiza con fork. El paquete
compartido requeriría primero generalizar la API de los componentes Nicolify, lo
que agrega un sprint adicional de abstracción.

### 3. Contexto 1-brand vs. N-brand

El criterio de anti-duplication.md para lift a shared es DRY threshold = 2 consumers.
Actualmente Vitalia es la única brand médica. Si Guestly o FitFlow adoptan tokens
médico-wellness similares, el lift se justifica.

Hoy: 1 consumer. Regla anti-duplication no aplica.

**Decisión parcial:** fork correcto en contexto single-brand consumer.

### 4. Madurez del sistema vs. espacio de experimentación

Los componentes Nicolify en `closer-studio/` y `brand-studio/` son producción
estable (PI-12 done, auditor APPROVED). Vitalia Slice 1 es iteración
exploratoria: nuevos patrones PHI (`PiiMaskedSpan`, `AuditedSection`),
nueva lógica de cobranza 3-capas, nuevos patrones agenda médica.

El fork permite experimentar sin riesgo de regresión sobre Nicolify.

**Decisión parcial:** fork da el sandbox necesario para patrones sin precedente
cross-brand (PHI masking, audit log trigger on render).

## Decisión

**Fork físico para Slice 1.**

Los componentes de Nicolify se copian a `vitalia/frontend/src/` con el siguiente
workflow de adaptación:

1. Identificar path origen en `nicolify/frontend/src/features/{domain}/components/`
2. Copiar al path destino en `vitalia/frontend/src/features/{domain}/components/`
   o `vitalia/frontend/src/components/shared/{subdomain}/`
3. Reemplazar tokens literales usando el adaptador de tokens:
   - `purple-*` → `vitalia-azul-marino` o `vitalia-purpura` (según semántica)
   - `slate-100` / `gray-100` → `vitalia-muted`
   - `slate-50` → `vitalia-bg`
   - `slate-*` (text) → `vitalia-text-muted` / `vitalia-text-faint`
   - Hex literals `#XXXXXX` → CSS var `hsl(var(--vitalia-X))`
4. Envolver superficies PHI con `<PiiMaskedSpan>` / `<RequireRole>` / `<AuditedSection>`
5. Reemplazar strings hardcodeados → `<FEATURE>_COPY.{namespace}.{key}` (copy.ts)
6. Adaptar hooks API → endpoints Vitalia (`/api/v1/vitalia/{module}/`)

**Token adapter (SSoT de la decisión de fork):**

| Token Nicolify | Token Vitalia | Justificación |
|---|---|---|
| `purple-600` | `vitalia-purpura` | Acento secundario equivalente |
| `purple-700` | `vitalia-azul-marino` | Primary CTA/brand anchor |
| `slate-50` | `vitalia-bg` | Fondo principal |
| `slate-100` | `vitalia-muted` | Chips, tool calls, empty states |
| `slate-200` | `vitalia-border` | Bordes estándar |
| `slate-400` | `vitalia-text-faint` | Texto disabled |
| `slate-500` | `vitalia-text-muted` | Texto secundario |
| `slate-900` | `vitalia-text` | Texto principal |
| `white` | `vitalia-surface` | Cards, modals |
| `green-*` (success) | `vitalia-success` | Estado pagado/confirmado |
| `yellow-*` (warning) | `vitalia-warning` | Estado pendiente |
| `red-*` (danger) | `vitalia-danger` | Error/cancelado |
| `blue-*` (info) | `vitalia-cian` | Info/badges/links |

## Consecuencias

### Positivas
- Vitalia Slice 1 entregado sin bloqueos de governance cross-brand.
- Patrones PHI (HIPAA-lite) aislados en brand vitalia — no contaminan Nicolify.
- Token set Vitalia completamente auditado en un solo PR (T-arch-1).
- Arch fitness test `test_no_hardcoded_colors.test.ts` cubre todo el tree vitalia.
- Libertad para iterar form patterns vitalia-specific (cobranza 3-capas, agenda médica).

### Negativas
- Code cross-brand duplicado hasta Slice 2 (aceptable: < DRY threshold 2 consumers).
- Actualizaciones upstream de Nicolify no se propagan automáticamente a Vitalia.
- Auditor debe comparar manualmente si un componente Vitalia deriva de Nicolify.

### Mitigaciones
- `test_no_hardcoded_colors.test.ts` arch fitness previene regresión de tokens.
- `anti-duplication.md` audit en cada PR compara diff > 50% cross-brand.
- Codificado en este ADR: el fork es explícito, no accidental.

## Camino Slice 2 — candidato `@luana/ui-medical`

Cuando una segunda brand opte-in tokens médico-wellness (Guestly wellness vertical,
FitFlow recovery tracking, o nuevo bootstrap brand salud), el patrón se convierte
en candidato para promotion a paquete compartido `@luana/ui-medical`.

Trigger de evaluación: **2 brands consumers del mismo patrón PHI o del mismo
sistema de tokens médicos**.

Workflow Slice 2 (cuando aplique):
1. Emitir promotion proposal en `docs/promotion-protocol/proposals/`
2. `/pm-vitalia` ratifica — `/architect` diseña API pública del paquete
3. Extraer componentes comunes a `core/luana-core-ui-medical/` (nuevo package)
4. Vitalia + segunda brand consumen via `@luana/ui-medical`
5. Eliminar fork en `vitalia/frontend/src/` (reemplazar con imports `@luana/ui-medical`)

El paquete `@luana/ui-medical` candidato incluiría:
- `AgentAvatar` (generalizado para N-agent-roster)
- `PiiMaskedSpan` + `RequireRole` + `AuditedSection` (PHI defense-in-depth)
- `DepositBadge` (payment status cross-brand)
- `ActivityStreamSticky` (si otra brand adopta actividad agéntic sticky)

## Referencias

- `vitalia/docs/architecture/design-system.md` — tokens SSoT que cementa la decisión de fork
- `vitalia/docs/product/stories/vitalia-ux-discovery/03-arch-fe.md` § 7 — decisión fork documentada
- `.claude/rules/anti-duplication.md` — DRY threshold y criterios de lift shared
- `docs/promotion-protocol/README.md` — workflow brand→core para Slice 2
- `pnpm-workspace.yaml` — workspace TS packages (`@luana/*`) para cuando aplique lift
