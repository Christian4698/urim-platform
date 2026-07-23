const DEFAULT_TIMEOUT_MS = 5_000;
const MAX_TIMEOUT_MS = 30_000;

const REQUIRED_DISABLED_DEPENDENCIES = [
  "bookmakers",
  "ml_models",
  "live",
  "real_betting",
  "prediction_creation"
] as const;

export type ApiErrorCode =
  | "configuration"
  | "timeout"
  | "network"
  | "http"
  | "invalid_json"
  | "invalid_response";

export class ApiClientError extends Error {
  readonly code: ApiErrorCode;
  readonly status?: number;

  constructor(code: ApiErrorCode, message: string, status?: number) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.status = status;
  }
}

export type FetchLike = (
  input: RequestInfo | URL,
  init?: RequestInit
) => Promise<Response>;

export type HealthResponse = {
  status: "ok";
  app_name: string;
  engine_name: string;
  phase: string;
};

export type ReadinessResponse = {
  ready: boolean;
  phase: string;
  dependencies: Record<string, string> & {
    database: "ok" | "unavailable";
    redis: "not_required";
    sports_providers: "disabled" | "ready";
    bookmakers: "disabled";
    ml_models: "disabled";
    live: "disabled";
    real_betting: "disabled";
    prediction_creation: "disabled";
  };
};

export type SystemAvailability = {
  api: "online";
  database: "available" | "unavailable";
  service: "available" | "degraded";
  phase: string;
};

export type ApiClientOptions = {
  baseUrl?: string;
  timeoutMs?: number;
  fetchImpl?: FetchLike;
};

export type SportsProviderStatus = {
  provider: "api-football";
  status:
    | "ready"
    | "disabled_by_configuration"
    | "disabled_missing_credential"
    | "degraded";
  enabled: boolean;
  configured: boolean;
  connected: boolean;
  last_success_at: string | null;
  quota_remaining_daily: number | null;
  quota_remaining_minute: number | null;
  priority_competition_count: number;
  season: number | null;
  max_requests_per_sync: number;
  prediction_creation_enabled: false;
  live_automatic_enabled: false;
  bookmakers_enabled: false;
  betting_enabled: false;
};

export type SportsCompetition = {
  provider_competition_id: number;
  name: string;
  kind: string | null;
  country_name: string | null;
  current_season: number | null;
  fetched_at: string;
  freshness_status: string;
};

export type SportsMatch = {
  provider_match_id: number;
  kickoff_at: string;
  status_short: string;
  status_long: string;
  home_team_name: string;
  away_team_name: string;
  goals_home: number | null;
  goals_away: number | null;
  freshness_status: string;
};

export type SportsSyncStatus = {
  provider: "api-football";
  latest: {
    run_id: string;
    sync_type: string;
    status: string;
    completed_at: string | null;
    request_count: number;
    records_inserted: number;
    records_duplicate: number;
    records_rejected: number;
    quota_remaining_daily: number | null;
    public_error_code: string | null;
  } | null;
  recent_errors: string[];
  read_only: true;
};

export type SportsFreshness = {
  as_of: string;
  threshold_minutes: number;
  resources: Array<{
    resource: string;
    latest_fetched_at: string | null;
    age_minutes: number | null;
    status: "fresh" | "stale" | "missing";
    row_count: number;
  }>;
  read_only: true;
};

export type SportsDataSnapshot = {
  provider: SportsProviderStatus;
  competitions: SportsCompetition[];
  today: SportsMatch[];
  upcoming: SportsMatch[];
  sync: SportsSyncStatus;
  freshness: SportsFreshness;
};

export type UrimApiClient = {
  getHealth: () => Promise<HealthResponse>;
  getReadiness: () => Promise<ReadinessResponse>;
  getSystemAvailability: () => Promise<SystemAvailability>;
  getSportsData: () => Promise<SportsDataSnapshot>;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isHealthResponse(value: unknown): value is HealthResponse {
  return (
    isRecord(value) &&
    value.status === "ok" &&
    typeof value.app_name === "string" &&
    value.app_name.length > 0 &&
    typeof value.engine_name === "string" &&
    value.engine_name.length > 0 &&
    typeof value.phase === "string" &&
    value.phase.length > 0
  );
}

function isReadinessResponse(value: unknown): value is ReadinessResponse {
  if (
    !isRecord(value) ||
    typeof value.ready !== "boolean" ||
    typeof value.phase !== "string" ||
    value.phase.length === 0 ||
    !isRecord(value.dependencies)
  ) {
    return false;
  }

  const dependencies = value.dependencies;
  const databaseStatus = dependencies.database;
  if (
    (databaseStatus !== "ok" && databaseStatus !== "unavailable") ||
    value.ready !== (databaseStatus === "ok") ||
    dependencies.redis !== "not_required"
  ) {
    return false;
  }

  if (
    dependencies.sports_providers !== "disabled" &&
    dependencies.sports_providers !== "ready"
  ) {
    return false;
  }

  return REQUIRED_DISABLED_DEPENDENCIES.every(
    (dependency) => dependencies[dependency] === "disabled"
  );
}

function isSportsProviderStatus(value: unknown): value is SportsProviderStatus {
  if (!isRecord(value)) {
    return false;
  }
  const allowedStatuses = [
    "ready",
    "disabled_by_configuration",
    "disabled_missing_credential",
    "degraded"
  ];
  return (
    value.provider === "api-football" &&
    typeof value.status === "string" &&
    allowedStatuses.includes(value.status) &&
    typeof value.enabled === "boolean" &&
    typeof value.configured === "boolean" &&
    typeof value.connected === "boolean" &&
    typeof value.priority_competition_count === "number" &&
    typeof value.max_requests_per_sync === "number" &&
    value.prediction_creation_enabled === false &&
    value.live_automatic_enabled === false &&
    value.bookmakers_enabled === false &&
    value.betting_enabled === false
  );
}

function isSportsCompetition(value: unknown): value is SportsCompetition {
  return (
    isRecord(value) &&
    typeof value.provider_competition_id === "number" &&
    typeof value.name === "string" &&
    typeof value.fetched_at === "string" &&
    typeof value.freshness_status === "string"
  );
}

function isSportsMatch(value: unknown): value is SportsMatch {
  return (
    isRecord(value) &&
    typeof value.provider_match_id === "number" &&
    typeof value.kickoff_at === "string" &&
    typeof value.status_short === "string" &&
    typeof value.status_long === "string" &&
    typeof value.home_team_name === "string" &&
    typeof value.away_team_name === "string" &&
    typeof value.freshness_status === "string"
  );
}

function isCollectionOf<T>(
  value: unknown,
  validator: (item: unknown) => item is T
): value is { items: T[]; count: number; read_only: true } {
  return (
    isRecord(value) &&
    Array.isArray(value.items) &&
    value.items.every(validator) &&
    typeof value.count === "number" &&
    value.count === value.items.length &&
    value.read_only === true
  );
}

function isSportsSyncStatus(value: unknown): value is SportsSyncStatus {
  if (
    !isRecord(value) ||
    value.provider !== "api-football" ||
    !Array.isArray(value.recent_errors) ||
    !value.recent_errors.every((error) => typeof error === "string") ||
    value.read_only !== true
  ) {
    return false;
  }
  if (value.latest === null) {
    return true;
  }
  return (
    isRecord(value.latest) &&
    typeof value.latest.run_id === "string" &&
    typeof value.latest.sync_type === "string" &&
    typeof value.latest.status === "string" &&
    typeof value.latest.request_count === "number" &&
    typeof value.latest.records_inserted === "number" &&
    typeof value.latest.records_duplicate === "number" &&
    typeof value.latest.records_rejected === "number"
  );
}

function isSportsFreshness(value: unknown): value is SportsFreshness {
  return (
    isRecord(value) &&
    typeof value.as_of === "string" &&
    typeof value.threshold_minutes === "number" &&
    Array.isArray(value.resources) &&
    value.resources.every(
      (resource) =>
        isRecord(resource) &&
        typeof resource.resource === "string" &&
        typeof resource.row_count === "number" &&
        ["fresh", "stale", "missing"].includes(String(resource.status))
    ) &&
    value.read_only === true
  );
}

function normalizeBaseUrl(value: string | undefined): string {
  if (!value?.trim()) {
    throw new ApiClientError(
      "configuration",
      "L’URL publique de l’API URIM n’est pas configurée."
    );
  }

  let parsedUrl: URL;
  try {
    parsedUrl = new URL(value.trim());
  } catch {
    throw new ApiClientError("configuration", "L’URL publique de l’API URIM est invalide.");
  }

  const isLocalHttp =
    parsedUrl.protocol === "http:" &&
    ["localhost", "127.0.0.1", "::1"].includes(parsedUrl.hostname);
  if (
    (parsedUrl.protocol !== "https:" && !isLocalHttp) ||
    parsedUrl.username ||
    parsedUrl.password ||
    (parsedUrl.pathname !== "/" && parsedUrl.pathname !== "") ||
    parsedUrl.search ||
    parsedUrl.hash
  ) {
    throw new ApiClientError("configuration", "L’URL publique de l’API URIM est invalide.");
  }

  return parsedUrl.origin;
}

async function requestJson<T>(
  baseUrl: string,
  path: string,
  validator: (value: unknown) => value is T,
  fetchImpl: FetchLike,
  timeoutMs: number
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  let response: Response;

  try {
    response = await fetchImpl(new URL(path, `${baseUrl}/`), {
      cache: "no-store",
      headers: { Accept: "application/json" },
      method: "GET",
      mode: "cors",
      referrerPolicy: "no-referrer",
      signal: controller.signal
    });
  } catch {
    if (controller.signal.aborted) {
      throw new ApiClientError("timeout", "Le service URIM n’a pas répondu à temps.");
    }
    throw new ApiClientError("network", "Le service URIM est indisponible.");
  } finally {
    clearTimeout(timeout);
  }

  if (!response.ok) {
    throw new ApiClientError("http", "Le service URIM a refusé la requête.", response.status);
  }

  if (!response.headers.get("content-type")?.toLowerCase().includes("application/json")) {
    throw new ApiClientError("invalid_response", "Le service URIM a retourné un format inattendu.");
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new ApiClientError("invalid_json", "Le service URIM a retourné une réponse invalide.");
  }

  if (!validator(payload)) {
    throw new ApiClientError(
      "invalid_response",
      "Le service URIM a retourné un contrat inattendu."
    );
  }

  return payload;
}

export function createApiClient(options: ApiClientOptions = {}): UrimApiClient {
  const baseUrl = normalizeBaseUrl(options.baseUrl ?? process.env.NEXT_PUBLIC_API_URL);
  const fetchImpl = options.fetchImpl ?? globalThis.fetch;
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;

  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0 || timeoutMs > MAX_TIMEOUT_MS) {
    throw new ApiClientError("configuration", "Le délai API URIM est invalide.");
  }

  const getHealth = () =>
    requestJson(baseUrl, "health", isHealthResponse, fetchImpl, timeoutMs);
  const getReadiness = () =>
    requestJson(baseUrl, "readiness", isReadinessResponse, fetchImpl, timeoutMs);

  return {
    getHealth,
    getReadiness,
    async getSportsData() {
      const [provider, competitions, today, upcoming, sync, freshness] =
        await Promise.all([
          requestJson(
            baseUrl,
            "api/v1/sports/provider",
            isSportsProviderStatus,
            fetchImpl,
            timeoutMs
          ),
          requestJson(
            baseUrl,
            "api/v1/sports/competitions",
            (value): value is { items: SportsCompetition[]; count: number; read_only: true } =>
              isCollectionOf(value, isSportsCompetition),
            fetchImpl,
            timeoutMs
          ),
          requestJson(
            baseUrl,
            "api/v1/sports/matches/today",
            (value): value is { items: SportsMatch[]; count: number; read_only: true } =>
              isCollectionOf(value, isSportsMatch),
            fetchImpl,
            timeoutMs
          ),
          requestJson(
            baseUrl,
            "api/v1/sports/matches/upcoming?days=7",
            (value): value is { items: SportsMatch[]; count: number; read_only: true } =>
              isCollectionOf(value, isSportsMatch),
            fetchImpl,
            timeoutMs
          ),
          requestJson(
            baseUrl,
            "api/v1/sports/sync/status",
            isSportsSyncStatus,
            fetchImpl,
            timeoutMs
          ),
          requestJson(
            baseUrl,
            "api/v1/sports/freshness",
            isSportsFreshness,
            fetchImpl,
            timeoutMs
          )
        ]);
      return {
        provider,
        competitions: competitions.items,
        today: today.items,
        upcoming: upcoming.items,
        sync,
        freshness
      };
    },
    async getSystemAvailability() {
      const [health, readiness] = await Promise.all([getHealth(), getReadiness()]);
      if (health.phase !== readiness.phase) {
        throw new ApiClientError(
          "invalid_response",
          "Les états système URIM ne sont pas cohérents."
        );
      }

      const databaseAvailable = readiness.dependencies.database === "ok";
      return {
        api: "online",
        database: databaseAvailable ? "available" : "unavailable",
        service: databaseAvailable ? "available" : "degraded",
        phase: readiness.phase
      };
    }
  };
}

export async function getSystemAvailability(): Promise<SystemAvailability> {
  return createApiClient().getSystemAvailability();
}
