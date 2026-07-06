import type {
  IntegrationMode,
  IntegrationProduct,
  ObservationProvenance,
  ProviderCapability,
  ProviderHealth,
  ProviderResponse,
  QualityFlag
} from "../types";

export const MOCK_SOURCE_VERSION = "integration-mock.v1";
export const MOCK_OBSERVED_AT = "2026-07-05T11:55:00.000Z";
export const MOCK_AVAILABLE_AT = "2026-07-05T11:58:00.000Z";
export const MOCK_FETCHED_AT = "2026-07-05T12:00:00.000Z";

const BASE_MOCK_FLAGS: QualityFlag[] = [
  "MOCK_DATA",
  "DEMO_ONLY",
  "NOT_FOR_PRODUCTION",
  "READ_ONLY",
  "AS_OF_SNAPSHOT",
  "LIVE_DISABLED",
  "NO_EXTERNAL_CALL"
];

export function makeMockHash(seed: string): string {
  let hash = 2166136261;

  for (let index = 0; index < seed.length; index += 1) {
    hash ^= seed.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }

  return `mock:${(hash >>> 0).toString(16).padStart(8, "0")}`;
}

export function createMockProvenance(options: {
  provider: string;
  provider_event_id: string;
  observed_at?: string;
  fetched_at?: string;
  available_at?: string;
  source_version?: string;
  quality_flags?: QualityFlag[];
  raw_hash_seed?: string;
}): ObservationProvenance {
  const qualityFlags = [...BASE_MOCK_FLAGS, ...(options.quality_flags ?? [])];
  const rawHashSeed =
    options.raw_hash_seed ?? `${options.provider}:${options.provider_event_id}:${MOCK_SOURCE_VERSION}`;

  return {
    provider: options.provider,
    provider_event_id: options.provider_event_id,
    observed_at: options.observed_at ?? MOCK_OBSERVED_AT,
    fetched_at: options.fetched_at ?? MOCK_FETCHED_AT,
    available_at: options.available_at ?? MOCK_AVAILABLE_AT,
    source_version: options.source_version ?? MOCK_SOURCE_VERSION,
    quality_flags: qualityFlags,
    raw_hash: makeMockHash(rawHashSeed)
  };
}

export function createMockResponse<TData>(options: {
  provider: string;
  provider_event_id: string;
  data: TData;
  request_id?: string;
  provider_timestamp?: string;
  schema_version?: string;
  warnings?: string[];
  quality_flags?: QualityFlag[];
  mode?: IntegrationMode;
  raw_hash_seed?: string;
}): ProviderResponse<TData> {
  const provenance = createMockProvenance({
    provider: options.provider,
    provider_event_id: options.provider_event_id,
    quality_flags: options.quality_flags,
    raw_hash_seed: options.raw_hash_seed
  });

  return {
    provider: options.provider,
    request_id: options.request_id ?? `mock-request:${options.provider_event_id}`,
    provider_event_id: options.provider_event_id,
    fetched_at: provenance.fetched_at,
    provider_timestamp: options.provider_timestamp ?? provenance.observed_at,
    http_status: 200,
    quota_remaining: null,
    raw_hash: provenance.raw_hash,
    payload_location: null,
    schema_version: options.schema_version ?? MOCK_SOURCE_VERSION,
    warnings: options.warnings ?? [],
    quality_flags: provenance.quality_flags,
    provenance,
    mode: options.mode ?? "mock",
    data: options.data
  };
}

export function createMockHealth(options: {
  product: IntegrationProduct;
  provider: string;
  capabilities: ProviderCapability[];
  mode?: IntegrationMode;
  notes?: string[];
}): ProviderHealth {
  return {
    product: options.product,
    provider: options.provider,
    status: "healthy",
    checked_at: MOCK_FETCHED_AT,
    mode: options.mode ?? "mock",
    capabilities: options.capabilities,
    live_enabled: false,
    real_provider_enabled: false,
    external_calls_enabled: false,
    notes: [
      "Mock provider only.",
      "No external calls, secrets, live betting, or real provider activation.",
      ...(options.notes ?? [])
    ]
  };
}
