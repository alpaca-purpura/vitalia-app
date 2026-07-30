// cap: __shared__
// story-origin: TBD
/**
 * marketing-shared — types re-exported for cross-story consumption (T-mk-fe-2..5)
 * downstream-regression-na: brand-local FE shared types; no cross-brand consumers
 */

export type {
  LucasRecommendation,
  RecommendationStage,
  RecommendationStatus,
  RejectReason,
} from "../marketing/types/lucas-recommendation";

export type {
  AttributionOrigin,
  AttributionOriginRow,
  AttributionMatrixResponse,
} from "../marketing/types/attribution";

export type {
  ProviderSlug,
  SyncStatus,
  ChannelSyncState,
} from "../marketing/types/channel";
