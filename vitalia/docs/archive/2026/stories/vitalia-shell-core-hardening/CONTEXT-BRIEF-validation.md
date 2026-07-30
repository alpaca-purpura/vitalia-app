# CONTEXT-BRIEF-validation — vitalia-shell-core-hardening

> Adversarial probe of `CONTEXT-BRIEF.md` (context-builder Haiku 4.5).
> Brand: vitalia · Phase: builder · Modules: shell, clinics, crm
> Validated: 2026-06-10T23:09:19Z (iter-1)
> Brief: vitalia/docs/product/stories/vitalia-shell-core-hardening/CONTEXT-BRIEF.md
> Audit log: vitalia/docs/product/stories/vitalia-shell-core-hardening/context-builder-logs/iter-1-2026-06-10T23-09-19Z.log

## Provenance note (R24/R28)

The `context-validator` subagent **is registered** (`.claude/agents/context-validator.md` confirmed present), BUT the running context-builder is itself a Haiku subagent with **no Agent/Task tool in its function set** — it cannot spawn a nested subagent in this harness. Per R24/R28 (validator pass is mandatory, silent skip = contract violation), the adversarial probe was executed **INLINE** by the context-builder using the validator's defined methodology (different-keyword re-scan + 3 random claim re-greps + 1 fetch re-verify). This is a transparency disclosure, not a skip. Verdict below is real (greps executed, output captured).

## Adversarial re-scan (DIFFERENT / synonym keywords)

Keywords the brief might have missed — re-scanned `vitalia/frontend/src/` + `core/@luana/`:

| Synonym keyword | Hits | Brief covered it? |
|---|---|---|
| `react-resizable-panels` / `<Group` / `PanelGroup` / `useDefaultLayout` / `minSize` | ShellOrganismLayout.tsx + ShellOrganismLayoutClient.tsx | ✅ YES (§4 module state + §15 react-resizable-panels ref + §2 Decisión A root cause) |
| `drawer` / `mobileDrawer` / `role="dialog"` / `Sheet` | useViewportGuard.ts + ShellOrganismLayout.tsx + TopBarGlobal.tsx + ValeriaSidebar | ✅ YES (§3 responsive drawer <1024 + §4 useViewportGuard) |
| `next-themes` / `useTheme` / `data-theme` | `app/providers.tsx` (wiring) + globals.css + ThemeToggle.tsx | ✅ YES (§2 Decisión C "wiring next-themes se conserva" + §15 Tailwind ref). **NEW detail surfaced:** the theme provider lives in `app/providers.tsx` — minor addition, not a gap. |
| `SubSubTabsBar` / N3-static | SubSubTabsBar.tsx confirmed | ✅ YES (§4 "N3-static, NO es el list/detail" — brief correctly distinguishes it from the list/detail N3) |

**No missed systems.** Every synonym keyword maps to a system already enumerated in §4/§7.

## Random claim re-verification (3 claims from §7/§5.5)

| Claim | Brief said | Re-grep result | Verdict |
|---|---|---|---|
| StaffWorkspaceShell imports brand-local EntitySubNavBar | "staff:24 imports `@/components/shared/shell-organism/EntitySubNavBar`" | L24 = `import { EntitySubNavBar } from "@/components/shared/shell-organism/EntitySubNavBar";` | ✅ EXACT |
| proxy.ts 307 redirect already exists | "`NextResponse.redirect` 307 (L65-67)" | L65-67 = `bareTenantLandingRedirect(...)` + `if (landingRedirect)` + `return NextResponse.redirect(...)` | ✅ EXACT |
| EntityWorkspaceLayout = named export + store-free | "`"use client"` + STORE-FREE (G2). Named export (NO default)" | L9-10 doc "STORE-FREE (G2)... subscribes to NO store" + L71 `export function EntityWorkspaceLayout` (no `export default`) | ✅ EXACT |

## §15 web fetch re-verify

`https://nextjs.org/docs` → version **16.2.9** (lastUpdated 2025-05-02). Repo runs Next `^16.2.3` (package.json confirmed). Brief's §15 summary (soft-nav vs hard-nav page, version-aware B1 note) is accurate. The fetch resolved to Getting Started index (redirect from `/building-your-application`) — the brief correctly points T-4 to `/docs/app/getting-started/linking-and-navigating`.

## Extra adversarial check

`shellMode` in non-shell-organism dirs (`app/`, `features/`, `lib/`): **0 hits**. Confirms the brief's §7 claim that the `shellMode` footprint (~13 files) is contained to `shell-organism/` + `stores/` + `__tests__/architecture/`. AC-1 grep-to-0 scope is accurate.

## Discrepancies

- **HIGH:** none.
- **MEDIUM:** none.
- **LOW:** 1 — the theme provider location (`app/providers.tsx`) was surfaced by the adversarial scan but not explicitly named in the brief; the brief covers dark wiring conceptually (§2 Decisión C). Cosmetic; builder will find it via grep. Not a faithfulness gap.

## Verdict

**No HIGH or MEDIUM discrepancies. Brief §7/§5.5 claims verified accurate (3/3 random + synonym re-scan clean). §15 fetch accurate.**

→ Seal flag at provisional value: **clean**. The 1 LOW (provider path) is added to brief §11 as informational, not a degradation.