export type IsoDateTime = string;
export type RawHash = string;

export type IntegrationMode = "mock" | "demo";
export type IntegrationProduct = "URIM";

export type IntegrationDecision =
  | "ADVICE"
  | "WATCH"
  | "NO_BET"
  | "INSUFFICIENT_DATA"
  | "SUSPENDED";

export type QualityFlag =
  | "MOCK_DATA"
  | "DEMO_ONLY"
  | "NOT_FOR_PRODUCTION"
  | "READ_ONLY"
  | "AS_OF_SNAPSHOT"
  | "LIVE_DISABLED"
  | "NO_EXTERNAL_CALL"
  | "MISSING_EXPLICIT";

export type ProviderCapability =
  | "football-fixtures"
  | "team-statistics"
  | "odds-value"
  | "weather"
  | "exchange-rate"
  | "match-news-events";

export interface DateWindow {
  from: IsoDateTime;
  to: IsoDateTime;
  as_of?: IsoDateTime;
}

export interface ObservationProvenance {
  provider: string;
  provider_event_id: string;
  observed_at: IsoDateTime;
  fetched_at: IsoDateTime;
  available_at: IsoDateTime;
  source_version: string;
  quality_flags: QualityFlag[];
  raw_hash: RawHash;
}

export interface ProviderResponse<TData> {
  provider: string;
  request_id: string;
  provider_event_id: string;
  fetched_at: IsoDateTime;
  provider_timestamp: IsoDateTime;
  http_status: 200;
  quota_remaining: number | null;
  raw_hash: RawHash;
  payload_location: string | null;
  schema_version: string;
  warnings: string[];
  quality_flags: QualityFlag[];
  provenance: ObservationProvenance;
  mode: IntegrationMode;
  data: TData;
}

export interface ProviderHealth {
  product: IntegrationProduct;
  provider: string;
  status: "healthy" | "degraded" | "disabled";
  checked_at: IsoDateTime;
  mode: IntegrationMode;
  capabilities: ProviderCapability[];
  live_enabled: false;
  real_provider_enabled: false;
  external_calls_enabled: false;
  notes: string[];
}

export interface IntegrationError {
  code:
    | "REAL_PROVIDER_DISABLED"
    | "LIVE_DISABLED"
    | "INSUFFICIENT_DATA"
    | "UNSUPPORTED_CAPABILITY";
  message: string;
  retryable: boolean;
  decision: IntegrationDecision;
}
