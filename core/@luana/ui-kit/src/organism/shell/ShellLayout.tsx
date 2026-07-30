// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * ShellLayout — brand-agnostic shell layout (SSR-safe wrapper, T-K2 port).
 *
 * Port of vitalia ShellOrganismLayout. Loads ShellLayoutClient via next/dynamic
 * with ssr:false.
 *
 * WHY ssr:false (do NOT remove): react-resizable-panels v4.11.1
 * dist/react-resizable-panels.js uses `storage: n = localStorage` as a default
 * parameter (bare-name ref) evaluated BEFORE any `typeof` guard → ReferenceError
 * during the Next.js SSR pass. No caller-side fix exists (default params run
 * first). The idiomatic Next.js workaround is a client-only dynamic import.
 *
 * SSR fallback: the brand-provided `skeletonSlot` (store-free) is the dynamic
 * `loading` fallback so the persisted shell store NEVER evaluates in
 * SSR/pre-hydration context (which would clobber user prefs on reload). When no
 * skeletonSlot is provided a minimal store-free placeholder is used (keeps the
 * #main-content skip-link target accessible immediately).
 */

import dynamic from "next/dynamic";
import type { ReactNode } from "react";
import type { ShellLayoutProps } from "./types";

/**
 * Default SSR skeleton — store-free, minimal. Renders the #main-content
 * skip-link target immediately. Brands SHOULD pass their own `skeletonSlot`
 * (e.g. a store-free TopBar) for a lower layout shift.
 */
function DefaultShellSkeleton() {
  return (
    <div
      className="flex h-screen flex-col overflow-hidden bg-background text-foreground"
      data-shell-ssr-skeleton="true"
    >
      <div className="h-12 shrink-0 border-b bg-card" aria-hidden="true" />
      <main
        id="main-content"
        tabIndex={-1}
        className="flex-1 min-h-0 overflow-hidden"
        aria-label="Cargando"
      />
    </div>
  );
}

/**
 * Module-level holder for the brand `skeletonSlot`. The dynamic `loading`
 * component receives no props, so the brand fallback is staged here at first
 * render (set once; the slot is a stable element the brand passes by prop). The
 * dynamic import itself is module-scope (no per-render remount churn).
 */
let brandSkeleton: ReactNode = null;

function LoadingFallback() {
  return <>{brandSkeleton ?? <DefaultShellSkeleton />}</>;
}

const ShellLayoutClient = dynamic(
  () =>
    import("./ShellLayoutClient").then((m) => ({
      default: m.ShellLayoutClient,
    })),
  {
    ssr: false,
    loading: LoadingFallback,
  },
);

/**
 * ShellLayout — main shell chrome entry point (brand-agnostic).
 *
 * Renders the full-screen layout client-side post-hydration. The brand wires
 * its catalog/store/routing/slots by prop (T-K1 contract). Named export per
 * FSD-Lite (no default export).
 */
export function ShellLayout(props: ShellLayoutProps) {
  if (props.skeletonSlot !== undefined) {
    brandSkeleton = props.skeletonSlot;
  }
  return <ShellLayoutClient {...props} />;
}
