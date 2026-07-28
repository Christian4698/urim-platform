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
  | "not_found"
  | "rate_limit_unavailable"
  | "service_unavailable"
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
    redis: "ok" | "unavailable";
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

export type KairosMarketProbabilities = {
  home_win: number;
  draw: number;
  away_win: number;
  home_or_draw: number;
  away_or_draw: number;
  home_or_away: number;
  over_2_5: number;
  under_2_5: number;
  btts: number;
};

export type KairosSuggestionReason = {
  code: string;
  message: string;
  impact: "positive" | "negative" | "neutral";
  category: "analytical" | "guardrail";
  critical: boolean;
};

export type KairosSuggestion = {
  suggestion_version: "kairos_daily_suggestions_v1";
  provider_match_id: number;
  kickoff_at: string;
  home_team_name: string;
  away_team_name: string;
  recommendation:
    | "Home Win"
    | "Away Win"
    | "Draw"
    | "Double Chance"
    | "Over 2.5"
    | "Under 2.5"
    | "BTTS"
    | "NO_BET";
  recommendation_code: string;
  kairos_score: number;
  confidence_level: "blocked" | "low" | "medium" | "high";
  risk_level: "high" | "elevated" | "guarded";
  no_bet: boolean;
  reasons: KairosSuggestionReason[];
  market_probabilities: KairosMarketProbabilities | null;
  data_quality_score: number;
  technical_confidence_score: number;
  feature_snapshot_hash: string;
  decision_hash: string;
  analysis_path: string;
  read_only: true;
  persisted: false;
  provider_calls: false;
  bookmaker_data_used: false;
  automatic_betting_enabled: false;
  live_automatic_enabled: false;
  not_for_betting: true;
};

export type KairosDailySuggestions = {
  local_date: string;
  timezone: "Africa/Kinshasa";
  as_of: string;
  suggestion_count: number;
  evaluated_match_count: number;
  skipped_unsafe_match_count: number;
  suggestions: KairosSuggestion[];
  warnings: string[];
  read_only: true;
  db_writes: false;
  provider_calls: false;
  automatic_betting_enabled: false;
  live_automatic_enabled: false;
  not_for_betting: true;
};

export type KairosAnalysis = {
  provider_match_id: number;
  kickoff_at: string;
  model_version: string;
  prediction_time: string;
  probabilities: {
    home_win: number;
    draw: number;
    away_win: number;
  } | null;
  market_probabilities: KairosMarketProbabilities | null;
  confidence_score: number;
  data_quality_score: number;
  reasons: Array<{
    code: string;
    message: string;
    direction: "home" | "draw" | "away" | "neutral";
  }>;
  warnings: Array<{
    code: string;
    message: string;
    severity: "info" | "warning" | "blocking";
  }>;
  safety_decision: "NO_BET" | "INSUFFICIENT_DATA";
  /**
   * Alias de compatibilité de safety_decision.
   * Il ne représente jamais une suggestion analytique.
   */
  decision: "NO_BET" | "INSUFFICIENT_DATA";
  analytical_suggestion: KairosSuggestion;
  /** Alias de compatibilité de analytical_suggestion. */
  suggestion: KairosSuggestion;
  analysis_status: "ready" | "insufficient_data";
  read_only: true;
  persisted: false;
  official_prediction_published: false;
  automatic_betting_enabled: false;
  live_automatic_enabled: false;
  not_for_betting: true;
};

export type UrimApiClient = {
  getHealth: () => Promise<HealthResponse>;
  getReadiness: () => Promise<ReadinessResponse>;
  getSystemAvailability: () => Promise<SystemAvailability>;
  getSportsData: () => Promise<SportsDataSnapshot>;
  getDailySuggestions: () => Promise<KairosDailySuggestions>;
  getKairosAnalysis: (
    providerMatchId: number,
    asOf?: string
  ) => Promise<KairosAnalysis>;
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
  const redisStatus = dependencies.redis;
  if (
    (databaseStatus !== "ok" && databaseStatus !== "unavailable") ||
    (redisStatus !== "ok" && redisStatus !== "unavailable") ||
    value.ready !== (databaseStatus === "ok" && redisStatus === "ok")
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

function isFiniteScore(value: unknown, maximum: number): value is number {
  return (
    typeof value === "number" &&
    Number.isFinite(value) &&
    value >= 0 &&
    value <= maximum
  );
}

function isKairosMarketProbabilities(
  value: unknown
): value is KairosMarketProbabilities {
  if (!isRecord(value)) {
    return false;
  }
  const fields = [
    "home_win",
    "draw",
    "away_win",
    "home_or_draw",
    "away_or_draw",
    "home_or_away",
    "over_2_5",
    "under_2_5",
    "btts"
  ] as const;
  if (!fields.every((field) => isFiniteScore(value[field], 1))) {
    return false;
  }
  return (
    Math.abs(
      Number(value.home_win) + Number(value.draw) + Number(value.away_win) - 1
    ) <= 0.000001 &&
    Math.abs(Number(value.over_2_5) + Number(value.under_2_5) - 1) <= 0.000001
  );
}

function isKairosSuggestion(value: unknown): value is KairosSuggestion {
  if (!isRecord(value)) {
    return false;
  }
  const recommendations = [
    "Home Win",
    "Away Win",
    "Draw",
    "Double Chance",
    "Over 2.5",
    "Under 2.5",
    "BTTS",
    "NO_BET"
  ];
  const confidenceLevels = ["blocked", "low", "medium", "high"];
  const riskLevels = ["high", "elevated", "guarded"];
  const safeProviderMatchId =
    typeof value.provider_match_id === "number" &&
    Number.isSafeInteger(value.provider_match_id) &&
    value.provider_match_id > 0;
  const safeReasons =
    Array.isArray(value.reasons) &&
    value.reasons.length <= 12 &&
    value.reasons.every(
      (reason) =>
        isRecord(reason) &&
        typeof reason.code === "string" &&
        typeof reason.message === "string" &&
        ["positive", "negative", "neutral"].includes(String(reason.impact)) &&
        ["analytical", "guardrail"].includes(String(reason.category)) &&
        typeof reason.critical === "boolean" &&
        (!reason.critical || reason.category === "guardrail")
    );
  const marketProbabilities =
    value.market_probabilities === null
      ? null
      : isKairosMarketProbabilities(value.market_probabilities)
        ? value.market_probabilities
        : undefined;
  return (
    value.suggestion_version === "kairos_daily_suggestions_v1" &&
    safeProviderMatchId &&
    typeof value.kickoff_at === "string" &&
    typeof value.home_team_name === "string" &&
    typeof value.away_team_name === "string" &&
    recommendations.includes(String(value.recommendation)) &&
    typeof value.recommendation_code === "string" &&
    isFiniteScore(value.kairos_score, 100) &&
    confidenceLevels.includes(String(value.confidence_level)) &&
    riskLevels.includes(String(value.risk_level)) &&
    typeof value.no_bet === "boolean" &&
    value.no_bet === (value.recommendation === "NO_BET") &&
    safeReasons &&
    marketProbabilities !== undefined &&
    (value.no_bet || marketProbabilities !== null) &&
    isFiniteScore(value.data_quality_score, 100) &&
    isFiniteScore(value.technical_confidence_score, 65) &&
    typeof value.feature_snapshot_hash === "string" &&
    /^[0-9a-f]{64}$/i.test(value.feature_snapshot_hash) &&
    typeof value.decision_hash === "string" &&
    /^[0-9a-f]{64}$/i.test(value.decision_hash) &&
    value.analysis_path ===
      `/api/v1/kairos/matches/${value.provider_match_id}/analysis` &&
    value.read_only === true &&
    value.persisted === false &&
    value.provider_calls === false &&
    value.bookmaker_data_used === false &&
    value.automatic_betting_enabled === false &&
    value.live_automatic_enabled === false &&
    value.not_for_betting === true
  );
}

function isKairosDailySuggestions(
  value: unknown
): value is KairosDailySuggestions {
  return (
    isRecord(value) &&
    typeof value.local_date === "string" &&
    value.timezone === "Africa/Kinshasa" &&
    typeof value.as_of === "string" &&
    Array.isArray(value.suggestions) &&
    value.suggestions.length <= 12 &&
    value.suggestions.every(isKairosSuggestion) &&
    value.suggestion_count === value.suggestions.length &&
    isFiniteScore(value.evaluated_match_count, 16) &&
    isFiniteScore(value.skipped_unsafe_match_count, 16) &&
    value.suggestion_count <= value.evaluated_match_count &&
    value.evaluated_match_count + value.skipped_unsafe_match_count <= 16 &&
    Array.isArray(value.warnings) &&
    value.warnings.length <= 4 &&
    value.warnings.every((warning) => typeof warning === "string") &&
    value.read_only === true &&
    value.db_writes === false &&
    value.provider_calls === false &&
    value.automatic_betting_enabled === false &&
    value.live_automatic_enabled === false &&
    value.not_for_betting === true
  );
}

function isKairosAnalysis(value: unknown): value is KairosAnalysis {
  if (
    !isRecord(value) ||
    typeof value.provider_match_id !== "number" ||
    !Number.isSafeInteger(value.provider_match_id) ||
    value.provider_match_id <= 0 ||
    typeof value.kickoff_at !== "string" ||
    typeof value.model_version !== "string" ||
    typeof value.prediction_time !== "string" ||
    !isFiniteScore(value.confidence_score, 65) ||
    !isFiniteScore(value.data_quality_score, 100) ||
    !Array.isArray(value.reasons) ||
    !Array.isArray(value.warnings) ||
    !["NO_BET", "INSUFFICIENT_DATA"].includes(String(value.safety_decision)) ||
    value.decision !== value.safety_decision ||
    !isKairosSuggestion(value.analytical_suggestion) ||
    !isKairosSuggestion(value.suggestion) ||
    value.analytical_suggestion.provider_match_id !== value.provider_match_id ||
    value.suggestion.provider_match_id !== value.provider_match_id
  ) {
    return false;
  }
  const probabilities = value.probabilities;
  const validProbabilities =
    probabilities === null ||
    (isRecord(probabilities) &&
      isFiniteScore(probabilities.home_win, 1) &&
      isFiniteScore(probabilities.draw, 1) &&
      isFiniteScore(probabilities.away_win, 1) &&
      Math.abs(
        probabilities.home_win + probabilities.draw + probabilities.away_win - 1
      ) <= 0.000001);
  const marketProbabilities = value.market_probabilities;
  const validMarketProbabilities =
    probabilities === null
      ? marketProbabilities === null
      : isRecord(probabilities) &&
        isFiniteScore(probabilities.home_win, 1) &&
        isFiniteScore(probabilities.draw, 1) &&
        isFiniteScore(probabilities.away_win, 1) &&
        isKairosMarketProbabilities(marketProbabilities) &&
        Math.abs(marketProbabilities.home_win - probabilities.home_win) <=
          0.000001 &&
        Math.abs(marketProbabilities.draw - probabilities.draw) <= 0.000001 &&
        Math.abs(marketProbabilities.away_win - probabilities.away_win) <=
          0.000001;
  return (
    validProbabilities &&
    validMarketProbabilities &&
    value.analytical_suggestion.decision_hash === value.suggestion.decision_hash &&
    value.analytical_suggestion.recommendation === value.suggestion.recommendation &&
    value.analytical_suggestion.no_bet === value.suggestion.no_bet &&
    (probabilities === null
      ? value.safety_decision === "INSUFFICIENT_DATA" &&
        value.analysis_status === "insufficient_data" &&
        value.analytical_suggestion.no_bet
      : value.safety_decision === "NO_BET" && value.analysis_status === "ready") &&
    value.read_only === true &&
    value.persisted === false &&
    value.official_prediction_published === false &&
    value.automatic_betting_enabled === false &&
    value.live_automatic_enabled === false &&
    value.not_for_betting === true
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
    throw await publicHttpError(response);
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

async function publicHttpError(response: Response): Promise<ApiClientError> {
  let publicCode: string | null = null;
  const contentType = response.headers.get("content-type")?.toLowerCase() ?? "";
  if (contentType.includes("application/json")) {
    try {
      const payload: unknown = await response.json();
      if (
        isRecord(payload) &&
        isRecord(payload.detail) &&
        typeof payload.detail.code === "string"
      ) {
        publicCode = payload.detail.code;
      }
    } catch {
      publicCode = null;
    }
  }

  if (
    response.status === 503 &&
    publicCode === "kairos_rate_limit_unavailable"
  ) {
    return new ApiClientError(
      "rate_limit_unavailable",
      "Le service de contrôle de débit Redis est indisponible. Les analyses Kairos sont temporairement bloquées par sécurité.",
      response.status
    );
  }
  if (
    response.status === 404 &&
    publicCode === "kairos_match_not_found_as_of"
  ) {
    return new ApiClientError(
      "not_found",
      "Aucun match n’est disponible pour cet identifiant et cet instant d’analyse.",
      response.status
    );
  }
  if (response.status === 503) {
    return new ApiClientError(
      "service_unavailable",
      "L’API URIM est temporairement indisponible.",
      response.status
    );
  }
  return new ApiClientError(
    "http",
    "Le service URIM a refusé la requête.",
    response.status
  );
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
    getDailySuggestions: () =>
      requestJson(
        baseUrl,
        "api/v1/kairos/suggestions/today",
        isKairosDailySuggestions,
        fetchImpl,
        timeoutMs
      ),
    getKairosAnalysis(providerMatchId: number, asOf?: string) {
      if (!Number.isSafeInteger(providerMatchId) || providerMatchId <= 0) {
        return Promise.reject(
          new ApiClientError(
            "configuration",
            "L’identifiant du match Kairos est invalide."
          )
        );
      }
      const query = new URLSearchParams();
      if (asOf !== undefined) {
        const parsedAsOf = new Date(asOf);
        if (
          !/(?:Z|[+-][0-9]{2}:[0-9]{2})$/.test(asOf) ||
          Number.isNaN(parsedAsOf.getTime())
        ) {
          return Promise.reject(
            new ApiClientError(
              "configuration",
              "L’instant d’analyse Kairos est invalide."
            )
          );
        }
        query.set("as_of", asOf);
      }
      const suffix = query.size ? `?${query.toString()}` : "";
      const request = requestJson(
        baseUrl,
        `api/v1/kairos/matches/${providerMatchId}/analysis${suffix}`,
        isKairosAnalysis,
        fetchImpl,
        timeoutMs
      );
      if (asOf === undefined) {
        return request;
      }
      return request.then((analysis) => {
        if (
          new Date(analysis.prediction_time).getTime() !==
          new Date(asOf).getTime()
        ) {
          throw new ApiClientError(
            "invalid_response",
            "L’analyse Kairos ne correspond pas à l’instant demandé."
          );
        }
        return analysis;
      });
    },
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
        service: readiness.ready ? "available" : "degraded",
        phase: readiness.phase
      };
    }
  };
}

export async function getSystemAvailability(): Promise<SystemAvailability> {
  return createApiClient().getSystemAvailability();
}
