// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * marketing feature — public API barrel
 * downstream-regression-na: brand-local FE feature barrel; no cross-brand consumers
 */

// Types
export type {
  RecommendationStage,
  RecommendationStatus,
  RejectReason,
  LucasRecommendation,
  LucasRecommendationsResponse,
  ApproveRecommendationResponse,
  RejectRecommendationResponse,
  UndoRecommendationResponse,
} from "./types/lucas-recommendation";

export type {
  BowtieStage,
  BowtieSummaryResponse,
  StageDetailResponse,
} from "./types/bowtie";

export type {
  AttributionOrigin,
  AttributionOriginRow,
  AttributionMatrixResponse,
} from "./types/attribution";

export type {
  ReferrerLeaderboardRow,
  ReferralsResponse,
} from "./types/referrals";

export type {
  ProviderSlug,
  SyncStatus,
  ChannelSyncState,
  ChannelMetricRow,
  ChannelDetailResponse,
  OAuthConnectResponse,
  SyncResponse,
} from "./types/channel";

export { marketingParsers } from "./types/url-state";
export type { MarketingTab, MarketingPeriod } from "./types/url-state";

// Copy
export { MARKETING_COPY } from "./copy";

// Hooks (queries)
export { useBowtieSummary } from "./api/use-bowtie-summary";
export type { UseBowtieSummaryOptions } from "./api/use-bowtie-summary";

export { useStageDetail } from "./api/use-stage-detail";
export type { UseStageDetailOptions } from "./api/use-stage-detail";

export { useChannelDetail } from "./api/use-channel-detail";
export type { UseChannelDetailOptions } from "./api/use-channel-detail";

export { useLucasRecommendations } from "./api/use-lucas-recommendations";

export { useAttributionMatrix } from "./api/use-attribution-matrix";
export type { UseAttributionMatrixOptions } from "./api/use-attribution-matrix";

export { useReferrals } from "./api/use-referrals";
export type { UseReferralsOptions } from "./api/use-referrals";

// Hooks (mutations)
export { useApproveRecommendation } from "./api/use-approve-recommendation";
export type { ApproveRecommendationVariables } from "./api/use-approve-recommendation";

export { useRejectRecommendation } from "./api/use-reject-recommendation";
export type { RejectRecommendationVariables } from "./api/use-reject-recommendation";

export { useUndoRecommendation } from "./api/use-undo-recommendation";
export type { UndoRecommendationVariables } from "./api/use-undo-recommendation";

export { useSyncChannel } from "./api/use-sync-channel";
export type { UseSyncChannelVariables } from "./api/use-sync-channel";

// Store
export { useMarketingStore } from "./store/marketing-store";

// Components (T-mk-fe-2)
export { MarketingBowtieSVG } from "./components/MarketingBowtieSVG";
export type { MarketingBowtieSVGProps } from "./components/MarketingBowtieSVG";

export { MarketingStageTabs } from "./components/MarketingStageTabs";
export type { MarketingStageTabsProps } from "./components/MarketingStageTabs";

export { MarketingLayout } from "./components/MarketingLayout";
export type { MarketingLayoutProps } from "./components/MarketingLayout";

export { StageDispatcher } from "./components/StageDispatcher";
export type { StageDispatcherProps } from "./components/StageDispatcher";

export { MarketingActivityFooter } from "./components/MarketingActivityFooter";
export type { MarketingActivityFooterProps } from "./components/MarketingActivityFooter";

// Components (T-mk-fe-3)
export { LucasStageRecommendationsCard } from "./components/LucasStageRecommendationsCard";
export type { LucasStageRecommendationsCardProps } from "./components/LucasStageRecommendationsCard";

export { LucasRecommendationDetailModal } from "./components/LucasRecommendationDetailModal";
export type { LucasRecommendationDetailModalProps } from "./components/LucasRecommendationDetailModal";

export { LucasApprovalModal } from "./components/LucasApprovalModal";
export type { LucasApprovalModalProps } from "./components/LucasApprovalModal";

export { LucasUndoChip } from "./components/LucasUndoChip";
export type { LucasUndoChipProps } from "./components/LucasUndoChip";

export { LucasRejectModal } from "./components/LucasRejectModal";
export type { LucasRejectModalProps } from "./components/LucasRejectModal";

// Components (T-mk-fe-5)
export { ConnectionBadge } from "./components/ConnectionBadge";
export type {
  ConnectionBadgeProps,
  ConnectionBadgeVariant,
} from "./components/ConnectionBadge";

export { ChannelBreakdownRow } from "./components/ChannelBreakdownRow";
export type { ChannelBreakdownRowProps } from "./components/ChannelBreakdownRow";

export { ChannelDetailSidebar } from "./components/ChannelDetailSidebar";
export type { ChannelDetailSidebarProps } from "./components/ChannelDetailSidebar";

export { ChannelConnectionWizard } from "./components/ChannelConnectionWizard";
export type { ChannelConnectionWizardProps } from "./components/ChannelConnectionWizard";

// Components (T-mk-fe-4)
export { AttributionMatrixWidget } from "./components/AttributionMatrixWidget";
export type { AttributionMatrixWidgetProps } from "./components/AttributionMatrixWidget";

export { ReferralsWidget } from "./components/ReferralsWidget";
export type { ReferralsWidgetProps } from "./components/ReferralsWidget";

export { AttractionStage } from "./components/AttractionStage";
export type { AttractionStageProps } from "./components/AttractionStage";

export { QualificationStage } from "./components/QualificationStage";
export type { QualificationStageProps } from "./components/QualificationStage";

export { ReservationStage } from "./components/ReservationStage";
export type { ReservationStageProps } from "./components/ReservationStage";

export { AdoptionStage } from "./components/AdoptionStage";
export type { AdoptionStageProps } from "./components/AdoptionStage";

export { ExpansionStage } from "./components/ExpansionStage";
export type { ExpansionStageProps } from "./components/ExpansionStage";
