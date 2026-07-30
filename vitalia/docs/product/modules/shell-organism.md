# Shell Organism — Vitalia Fase 1 UI Foundation

> Brand-local module. NO cross-brand consumers. UI shell chrome only (no PHI).

## Propósito

El shell-organism es el contenedor raíz del UI Vitalia post-login. Define el layout 50/50 split en modo agéntico (ValeriaPanel a la izquierda como copiloto conversacional · AppPanel a la derecha con ribbon de agentes Lisa/Lucas/Adrián/Valeria/Camila + Configurar) y soporta un modo web alternativo (Valeria collapsed a rail · App 100% para flujos web tradicionales).

Es el primer building block de la Fase 1 UI Foundation antes de F1-S5..S10 que llenarán los slots con contenido real (history, chat, ribbon 6 tabs, sub-tabs, empty-states).

## Capabilities <!-- AUTO-GENERATED — no editar a mano -->

- [`shell.empty-states`](../capabilities/shell-organism/empty-states.yaml) — SubTabContent dispatcher PLACEHOLDER_MAP 22 entries + 6 placeholders especiales con mockup parity (Lisa Servicios·Adrián Embudo·Adrián Inbox con Takeover UX + sales_studio parity·Camila Voz·Valeria Agenda enriquecida·Config Conexiones) + 16 EmptyState genéricos · 18 NEW moléculas + 8 organismos · ★ cierra Fase 1 (status: live, 2026-05-26, story F1-S10)
- [`shell.layout-5050`](../capabilities/shell-organism/layout-5050.yaml) — Layout root split 50/50 agentic + web mode alternativo + mobile triple-main pattern (status: live, 2026-05-23, story F1-S4)
- [`shell.ribbon`](../capabilities/shell-organism/ribbon.yaml) — Ribbon horizontal 5 RibbonTabs (Lisa·Lucas·Adrián·Valeria·Camila) + 1 ConfigTab IconButton · WAI-ARIA tablist + roving tabindex · active state URL-derived via extractAgentFromPath · Avatar fallback graceful (status: live, 2026-05-25, story F1-S7)
- [`shell.routing`](../capabilities/shell-organism/routing.yaml) — Routing tree shell-organism Next.js 16: proxy.ts clerkMiddleware + [agent]/[subtab]/page.tsx dynamic con isValidAgent + isValidSubtab + not-found.tsx jerárquico outer+inner + default landing valeria/agenda (status: live, 2026-05-25, story F1-S9)
- [`shell.sub-tabs`](../capabilities/shell-organism/sub-tabs.yaml) — SubTabsBar línea 2 con 22 sub-tabs distribuidos 4·5·4·2·4·3·0[mateo] · catalog SSoT RIBBON_SUBTABS extension agent-catalog.ts (status: live, 2026-05-25, story F1-S8)
- [`shell.valeria-chat`](../capabilities/shell-organism/valeria-chat.yaml) — Valeria chat panel skeleton (ChatHeader + ChatMessages + ChatComposer + chat-store zustand + mock responses canned) consumido por ValeriaSidebar (status: live, 2026-05-25, story F1-S6)
- [`shell.valeria-sidebar`](../capabilities/shell-organism/valeria-sidebar.yaml) — Valeria sidebar transpuesta full/rail/collapsed modes con ValeriaRail icon-only 60px + ValeriaHistory expandable groups + ValeriaChatSlot wrapper (status: live, 2026-05-24, story F1-S5)

<!-- END AUTO-GENERATED -->
<!-- F1 closure 2026-05-26: auto-gen script para esta sección NO existe aún (R3 brand-docs-schema señaló como auto-gen aspirational). Hasta entonces, mantenimiento manual al merge: /pm-vitalia debe agregar nueva capability al cerrar story. Backlog item: crear scripts/regen_modules_md.py + integrarlo en Makefile target `make modules-md`. -->

## Decisiones cardinales

- **Triple-main pattern CSS-driven:** 3 `<main id="main-content">` elements mutually-exclusive via Tailwind (`md:hidden` mobile + `hidden md:block` agentic + `hidden md:grid` web). Solo UNO es visible per viewport. Skip-link `#main-content` resolve al visible.
- **react-resizable-panels v4 SSR workaround:** `useDefaultLayout` usa bare-name `localStorage` default param que crashea SSR → split en `ShellOrganismLayout` (wrapper) + `ShellOrganismLayoutClient` (real impl) via `next/dynamic({ssr:false})`. Skeleton fallback mantiene TopBarGlobal + #main-content para skip-link accesibilidad inmediata.
- **minSize PERCENT (no pixels):** v4 trata numeric minSize como pixels (useless para layout responsive). Pasamos string `"${minValeriaPct}%"` para enforce native drag clamp. ResizeObserver del container recalcula percent dinámicamente desde pixels cementados (MIN_VALERIA_PX 620 full / 360 rail · MIN_APP_PX 480).
- **Snap-up Fix A via useGroupRef:** useEffect post-ResizeObserver detecta layout persisted < minSize → setLayout([minPct, 100-minPct]) imperativo. Resuelve hydration race condition para drag-clamp (drag-after-rail edge case DEFERRED a F1-S5/S6 lifecycle work).
- **valeriaState default='full':** override Design Contract §6.1 ('rail') — matches mockup ratificado iter 4 Chris 2026-05-23.
- **Showcase pattern parity F1-S0..S3:** route `/test-stack/shell-layout` para Playwright E2E sin Clerk auth fixture (paths public via `proxy.ts` matcher).

## Anti-objetivos cementados

- NO incluir contenido del ValeriaPanel (eso es F1-S5 + F1-S6)
- NO incluir contenido del AppPanel (eso es F1-S7 + F1-S8 + F1-S10)
- NO modificar TopBarGlobal/LogoMark/ThemeToggle/TenantSwitcher (F1-S1/S2/S3 REUSE)
- NO touch route group `(dashboard)/` legacy (paralelo route group `(shell-organism)/`)
- NO cross-brand consumers (brand-local Vitalia)

## Referencias

- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` — atomic design SSoT del shell completo (componentes + props + estados visuales)
- Story archive: `vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/` (snapshot inmutable F1-S4)
- Mockups ratificados: `vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/mockups/{shell-layout-agentic,shell-layout-web}.html` (iter 4 Chris 2026-05-23)
- Learning: `vitalia/docs/learnings/2026-05-23-shell-layout-race-condition-defer.md` (race condition pattern promotable cross-brand candidate)
- Follow-up: `vitalia/docs/product/stories/vitalia-fase1-shell-layout-5050-race-fix/` (state=parked, race fix tracking)
