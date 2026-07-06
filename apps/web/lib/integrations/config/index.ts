import type { IntegrationMode } from "../types";

export interface IntegrationRuntimeConfig {
  mode: IntegrationMode;
  requested_mode: string | undefined;
  live_enabled: false;
  real_providers_enabled: false;
  backend_proxy_enabled: false;
  external_api_calls_enabled: false;
  activation_gate: "MOCK_ONLY";
  notes: string[];
}

export const integrationEnvironmentVariables = [
  "NEXT_PUBLIC_URIM_INTEGRATION_MODE",
  "URIM_INTEGRATION_PROVIDER_MODE",
  "URIM_ENABLE_REAL_API_PROVIDERS",
  "ENABLE_LIVE"
] as const;

function readPublicIntegrationMode(): string | undefined {
  if (typeof process === "undefined") {
    return undefined;
  }

  return process.env.NEXT_PUBLIC_URIM_INTEGRATION_MODE;
}

function normalizeMode(value: string | undefined): IntegrationMode {
  return value === "demo" ? "demo" : "mock";
}

const requestedMode = readPublicIntegrationMode();

export const integrationRuntimeConfig: IntegrationRuntimeConfig = Object.freeze({
  mode: normalizeMode(requestedMode),
  requested_mode: requestedMode,
  live_enabled: false,
  real_providers_enabled: false,
  backend_proxy_enabled: false,
  external_api_calls_enabled: false,
  activation_gate: "MOCK_ONLY",
  notes: [
    "DEMO/MOCK is the default and only active integration mode.",
    "LIVE is forcibly disabled in this frontend scaffold.",
    "Future real providers must be backend adapters behind explicit onboarding gates."
  ]
});

export function assertMockOnlyIntegrationConfig(config: IntegrationRuntimeConfig): void {
  if (
    config.live_enabled ||
    config.real_providers_enabled ||
    config.backend_proxy_enabled ||
    config.external_api_calls_enabled ||
    config.activation_gate !== "MOCK_ONLY"
  ) {
    throw new Error("Integration config rejected: LIVE or real providers are not enabled.");
  }
}
