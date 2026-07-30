---
proposal_id: 2026-06-16-collapsible-section-ui-kit
status: accepted
date: 2026-06-16
accepted_at: 2026-06-16
proposed_by: /architect (vitalia-fase2-lisa-servicios G round 1 reconcile)
accepted_by: Chris             # ratificado 2026-06-16 (G round 1 · "dale, ratificá la promotion y arrancá T-R0 + T-R1/T-R2 en paralelo"). T-R0 buildea CollapsibleSection en @luana/ui-kit (hub-scoped lift · wip/vitalia).
target_package: core/@luana/ui-kit
origin_brand: vitalia
origin_story: vitalia-fase2-lisa-servicios (reconcile delta · T-R0)
risk: low (aditivo · opt-in · backward-compatible · composes existing exported primitives)
---

# CollapsibleSection · molécula colapsable de sección en @luana/ui-kit

**Qué:** nueva molécula `CollapsibleSection` que compone los primitivos YA exportados de `@luana/ui-kit`
(`accordion` Radix + `Group` con barrita de agente + GroupHeader, canon §2.6). Header = título +
summary/contador-de-campos + acento de agente (left strip, reusa `Group.accentVar`); body colapsable;
`defaultOpen`. CERO edición a `accordion.tsx`/`Group.tsx`/`collapsible.tsx` — solo composición + 1 archivo nuevo + export.

**Por qué core (cross-brand reuse):** Chris ratificó en G (2026-06-16) que esta molécula vive en
`@luana/ui-kit` para reuso cross-brand real — nicolify/comunify heredan workspaces de entidad con fichas
seccionadas colapsables. El patrón "sección con cabecera + contador + body colapsable + acento de agente"
es genérico (no vitalia-specific). Mantenerlo brand-local generaría mirror cross-brand (prohibido,
`anti-duplication.md`). 1er consumidor = vitalia `lisa-servicios` ResumenView (6 secciones colapsables).

**Motivación (caso origen):** el workspace de servicios renderiza 6 grupos `<Group>` planos/expandidos; el
mockup ratificado (`servicio-workspace.html:497`) dicta 6 grupos COLAPSABLES (Identidad abierto, resto
cerrado, click toggle, contador "N campos"). Además vitalia arrastra un `accordion.tsx` duplicado local
(`vitalia/frontend/src/components/ui/accordion.tsx`) que es copia del Radix accordion — `CollapsibleSection`
es la primitiva core que lo reemplaza. **Nota de scope:** el dup local tiene 2 consumidores vivos fuera de
esta story (`features/mateo/components/agenda/{CobrarSaldoSubform,AppointmentDrawer}.tsx`), así que su BORRADO
+ repoint de mateo se difiere a un cleanup scoped aparte (NO se bundlea en este lift ni en T-R3) — anti-duplication
reconocido sin scope creep cross-feature.

**API (contrato — SSoT en `vitalia/docs/product/stories/vitalia-fase2-lisa-servicios/03-arch-reconcile-delta.md § Part D`):**
```tsx
export interface CollapsibleSectionProps {
  title: string;
  defaultOpen?: boolean;                 // @default false
  summary?: React.ReactNode;             // ej. "6 campos" (contador en el header)
  accentVar?: string;                    // "--agent-lisa" (reusa Group.accentVar · token-driven, nunca hex)
  accentClass?: string;                  // alt: "border-l-agent-lisa"
  hasError?: boolean;                    // estado de error semántico (delega a Group)
  missingFields?: string[];              // alerta inline de faltantes (delega a GroupHeader)
  children: React.ReactNode;             // body colapsable
  className?: string;
}
```
Composición: `Group` (outer · acento + error border + card) → `Accordion`/`AccordionTrigger` (single-item,
`collapsible`, `defaultOpen`) en el header con `title`+`summary`+chevron → `AccordionContent` con `children`.
`defaultOpen` → `defaultValue` Radix (uncontrolled). Sin `value`/`onValueChange` controlados por ahora (YAGNI).

**Consumers:**
- **Ahora:** vitalia `lisa-servicios` ResumenView (6 CollapsibleSection · reemplaza 6 `<Group>` planos). Ticket
  consumidor = T-R3 (GATED `depends_on: [esta proposal accepted]`). El borrado del `accordion.tsx` dup se difiere
  (consumidores mateo vivos · cleanup scoped aparte).
- **Después:** nicolify / comunify (workspaces de entidad con fichas seccionadas colapsables).

**Verificación (ejecutor del lift):**
- Unit test nuevo `CollapsibleSection.test.tsx`: title + summary + children render · `defaultOpen` abre · click
  toggle · `accentVar` aplica el left strip · `missingFields` muestra el alert inline.
- Tests existentes `accordion` + `Group` + `collapsible` siguen verdes (regression_guard · additive only).
- Downstream: ninguna otra brand consume aún al momento del lift → cero regresión cross-brand; vitalia consume en T-R3.
- Export agregado a `core/@luana/ui-kit/src/index.ts`. Bump semver minor (aditivo).

**Ejecutor (T-R0):** ticket de lift owned por `/pm-luana` promotion gate (NO builder vitalia). Edición scoped
SOLO a `core/@luana/ui-kit/src/CollapsibleSection.tsx` (NEW) + `index.ts` (export) + `__tests__/CollapsibleSection.test.tsx`.
Worktree: hub-scoped lift o worktree core efímero. NO toca semántica de `accordion`/`Group`/`collapsible`.

**Bloqueo aguas abajo:** T-R3 (vitalia FE ResumenView fidelity) está GATED hasta que esta proposal pase a
`accepted` y T-R0 se construya en ui-kit. Sin la molécula exportada, T-R3 no puede consumirla.
