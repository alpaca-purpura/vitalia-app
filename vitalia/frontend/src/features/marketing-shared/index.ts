// cap: __shared__
// story-origin: TBD
/**
 * marketing-shared — public API barrel for cross-story consumption
 * Used by T-mk-fe-2..5 (components, pages) to import shared types without circular deps
 * downstream-regression-na: brand-local FE shared barrel; no cross-brand consumers
 */

export type {
  LucasRecommendation,
  RecommendationStage,
  RecommendationStatus,
  RejectReason,
  AttributionOrigin,
  AttributionOriginRow,
  AttributionMatrixResponse,
  ProviderSlug,
  SyncStatus,
  ChannelSyncState,
} from "./types";
