// Leaf hooks (no feature module deps) — exported from @luana/hooks
export * from "./use-debounce";
export * from "./use-intersection-observer";
export * from "./use-is-mounted";
export * from "./use-local-storage";
export * from "./use-viewport";
// SSR-safe Zustand persisted store factory + rehydration hook (lift 2026-05-29 desde vitalia / ADR-vitalia-006)
export * from "./create-ssr-safe-persisted-store";
export * from "./use-store-hydration";
// Module-coupled hooks are NOT re-exported from the barrel — they import the consuming app's
// `@/features/*` paths which only resolve in ONE specific brand app, so re-exporting them here
// breaks every OTHER consumer (caught live: /showcase 500 in vitalia — vitalia has no
// `@/features/copilot/*`). They remain available via their explicit subpath exports
// (`@luana/hooks/use-copilot-offset`, see package.json#exports) for the app that owns those paths.
// export * from "./use-copilot-offset";   // app-coupled (@/features/copilot) — subpath only
// export * from "./use-shell-mutex";      // requires @/components/shared + @/stores — T-12
// export * from "./use-currency-catalog"; // requires @/lib/api — T-12
// Autosave primitive — primitiva de autoguardado compartida (ADR-012, build-autosave-primitive-luana T-1)
export { useAutosave } from "./useAutosave";
export type { AutosaveStatus, UseAutosaveOptions, UseAutosaveReturn } from "./useAutosave";
