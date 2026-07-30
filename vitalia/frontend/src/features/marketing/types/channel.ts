// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * Channel integration domain types — mirror of BE ChannelDetailResponse (camelCase)
 * downstream-regression-na: brand-local FE type; consumed by marketing feature only
 */

export type ProviderSlug = "meta_ads" | "google_ads";

export type SyncStatus = "idle" | "running" | "error" | "disconnected";

export type ChannelSyncState = {
  provider: ProviderSlug;
  lastSyncAt: string | null; // ISO 8601 UTC
  lastSuccessAt: string | null; // ISO 8601 UTC
  lastError: string | null;
  status: SyncStatus;
  enabled: boolean;
  accountId: string | null;
};

export type ChannelMetricRow = {
  provider: ProviderSlug;
  channelSlug: string;
  campaignId: string | null;
  campaignName: string | null;
  metricDate: string; // ISO 8601 date
  impressions: number | null;
  clicks: number | null;
  conversions: number | null;
  spendCents: number | null;
  currency: string | null;
};

export type ChannelDetailResponse = {
  provider: ProviderSlug;
  syncState: ChannelSyncState;
  metrics: ChannelMetricRow[];
};

export type OAuthConnectResponse = {
  authorizationUrl: string;
  state: string;
};

export type SyncResponse = {
  jobId: string;
  status: "queued" | "running";
  enqueuedAt: string; // ISO 8601 UTC
};
