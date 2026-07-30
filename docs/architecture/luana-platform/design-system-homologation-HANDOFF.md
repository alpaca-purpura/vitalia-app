# Design System Homologation — HANDOFF para arranque limpio

> **★ ARCHIVADO (génesis) 2026-06-25 — homes vivos: [ADR-016](ADR-016-design-system-inventory-governance.md) (gobernanza) + `design-system-canon.md` (contratos) + `core-ds-foundation/checkpoint.md` (build). No usar como fuente.**
>
> **★ SUPERSEDED 2026-06-08:** el showcase fue RATIFICADO (8 rondas /po-ux) y el build se **consolidó en UNA story**: `docs/product/stories/core-ds-foundation/` (Fase 0+1+2). El contrato + ejemplos de código viven en `docs/architecture/luana-platform/design-system-canon.md`. Los bindings de skills/rule ya están hechos. **Para retomar: leé `core-ds-foundation/checkpoint.md` + `design-system-canon.md` → `/architect brand: platform core-ds-foundation`.** Las stories `S-CORE-DS-*` listadas abajo NO se crearon por separado (fusionadas). Lo de abajo es histórico.

> Bootstrap para retomar en **conversación nueva**. Leé esto + los 3 artefactos linkeados y arrancá. Owner: `/pm-luana`. Origen: sesión 2026-06-06/07 (Chris: "el dev-team crea cada interfaz a su forma → se siente otra app; homologar todo de una vez").

## TL;DR

Homologar la UI cross-brand con un **design system de 5 capas en `core/@luana/`** + **enforcement mecánico** (porque el criterio no sostiene: vitalia tiene tokens+skill+rule D1 y aun así driftea 368 veces). **Ratificado por Chris 2026-06-07.**

## Estado (todo ratificado/accepted)

| Artefacto | Path | Estado |
|---|---|---|
| Doctrina | `docs/architecture/luana-platform/ADR-014-design-system-homologation.md` | **accepted** |
| Plan + lift | `docs/promotion-protocol/proposals/2026-06-07-design-system-homologation.md` | **accepted** |
| Outcome umbrella (hogar) | `docs/product/outcomes/luana-core-ui-foundation.md` | refining · absorbió las 3 piezas nuevas (status 2026-06-07) |
| Primera primitiva (learning) | `vitalia/docs/learnings/2026-06-06-n3-entity-workspace-layout-from-nicolify.md` | EntityWorkspaceLayout |

## Las 3 piezas que faltaban (vs el trabajo previo)

El outcome `luana-core-ui-foundation` (2026-05-21) ya tenía package + átomos + shell-organism (lifts `ui-extraction` + `lift-shell-organism` **accepted**). **Faltaban:**
1. **Capa 3 — layout-primitives de contenido** (`Page/PageHeader/Section/Toolbar/FilterBar/EmptyState/ErrorState/DetailLayout/FormLayout/EntityWorkspaceLayout` + archetypes) → `@luana/ui-kit`.
2. **Enforcement mecánico:** spacing scale en `@luana/design-tokens` + eslint `no-arbitrary-value`/tailwind-lock + arch-test layout.
3. **Adopción comprehensiva** (todas las hojas, no slice-by-slice — req Chris HARD).

## Ruta (la secuencia)

```
TRACK A (independiente · arranca YA · sirve el req#2 desde el día 1)
  S-CORE-DS-TOKENS-LOCK  ── Fase 0 quick-win
    · escala spacing en @luana/design-tokens (hoy solo z-index)
    · eslint no-arbitrary-value (allowlist ratchet shrink-only)
    · frena el drift NUEVO de inmediato · no toca código de feature
    Owner: /pm-luana → /po(-ux) define escala → /architect → /dev-team

TRACK B (gateado · el outcome ya gatea "no arrancar encima de las 4 stories abiertas")
  1. Cerrar las 4 abiertas:  shell-valeria-responsive (refined→build) · lisa-doctores · adrian-embudo · nicolify abel-icp
  2. Liftear shell → @luana/ui-kit  (proposal lift-shell-organism, accepted)
  3. S-CORE-DS-LAYOUT-PRIMITIVES  ── construir las ~10 primitivas + archetypes en @luana/ui-kit
                                     (EntityWorkspaceLayout = la primera; shell-valeria-responsive punto 7 ya la porta)
  4. S-{brand}-DS-ADOPTION × vitalia/nicolify/comunify  ── COMPREHENSIVA (todas las hojas; vitalia migra los 368)
```

> **b1/b2 de shell-valeria-responsive RESUELTO:** queda **b1** (cerrar abiertas → liftear → homologar), consistente con el gate que el outcome ya tenía. Fase 0 (Track A) es la única excepción que puede ir antes.

## Dónde intervenís vos (Chris)

1. ✅ Ratificaste ADR-014 + proposal (hecho).
2. **Track A:** ratificar la **escala de spacing** (qué valores: 4/8/12/16/24… o tu ritmo) + confirmar encender el lock por marca empezando por vitalia.
3. **Track B:** ratificar el **inventario de layout-primitives** (la lista de ~10 nombres/responsabilidades) + sus mockups/contratos (po-ux 2-rondas si hay UI nueva).
4. Firmas de demo (chris_verify) al cierre de cada story (DoD #37).
5. Confirmar el orden de cierre de las 4 abiertas (o delegarlo a cada /pm-{brand}).

## Primer paso en la conversación nueva (recomendado)

**Arrancar Track A** (independiente + sirve el req#2 ya):

```
/pm-luana  →  "arrancá S-CORE-DS-TOKENS-LOCK (Fase 0 design-system homologation)"
```

Eso abre: definir la escala spacing (con vos) → /architect ready package → /dev-team build en `@luana/design-tokens` + la regla eslint. En paralelo, las 4 stories abiertas siguen cerrando (Track B) sin bloquear.

(Alternativa si preferís: cerrar primero las 4 abiertas y arrancar todo Track B junto — pero perdés el "frena el drift ya" de Fase 0.)

## Anti-duplicación (recordatorio)

NO crear un design system nuevo: `@luana/ui-kit` + `@luana/design-tokens` YA existen + el outcome `luana-core-ui-foundation` es el hogar. Esto EXTIENDE, no recrea.

## Referencias

- ADR-014 (doctrina) · proposal 2026-06-07 (plan) · outcome luana-core-ui-foundation (hogar, status 2026-06-07)
- `ADR-012-autosave-primitive-platform.md` (patrón hermano) · `ADR-008-luana-core-ui-shadcn-cli-pattern.md` (distribución CLI)
- `.claude/rules/frontend-visual-fidelity.md` (D1) · `.claude/rules/anti-duplication.md`
