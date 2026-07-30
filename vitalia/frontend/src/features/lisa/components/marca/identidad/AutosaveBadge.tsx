// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * AutosaveBadge.tsx — Re-export from shared location.
 *
 * The actual implementation lives in components/marca/shared/AutosaveBadge.tsx
 * because it is shared across T-5 (Identidad), T-6 (Voz y tono), T-7 (Presencia).
 * This barrel re-export lets tests and imports use the local feature path.
 *
 * T-5 vitalia-fase2-lisa-marca
 * downstream-regression-na: brand-local vitalia FE re-export; no cross-brand consumers
 */

export {
  AutosaveBadge,
  type AutosaveBadgeProps,
  type AutosaveStatus,
} from "@/components/marca/shared/AutosaveBadge";
