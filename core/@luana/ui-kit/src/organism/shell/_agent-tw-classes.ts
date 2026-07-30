// cap: platform.lift-shell-chrome-ui-kit
/**
 * _agent-tw-classes.ts — brand-agnostic Tailwind class lookup via AgentClassBundle injection.
 *
 * Kit version: catalog is injected by brand (via getAgentClasses prop), NOT imported from
 * @/lib/agent-catalog. JIT-static color literals STAY brand-side — brand defines the
 * getAgentClasses fn that returns explicit class string literals.
 *
 * For direct lookup (TypingIndicator / DelegateMarker / SubTab / ChatHeader etc.),
 * components receive `getAgentClasses` as a prop and call it with the agent slug.
 *
 * This file re-exports the types and provides barrel-friendly access.
 *
 * CRITICAL: Tailwind v4 JIT purges dynamic class names (e.g. `bg-${agent}-soft`).
 * ALL class names MUST be statically knowable — they live in the BRAND, returned
 * by the injected getAgentClasses fn.
 *
 * spec_anchor: 03-arch.md § API contract + Decisión A (catalog/store por prop)
 * Named exports only (NO default) per FSD-Lite enforce.
 */

export type { AgentClassBundle, GetAgentClasses } from "./types";
