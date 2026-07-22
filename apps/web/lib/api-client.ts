const DEFAULT_TIMEOUT_MS = 5_000;
const MAX_TIMEOUT_MS = 30_000;

const REQUIRED_DISABLED_DEPENDENCIES = [
  "sports_providers",
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
    sports_providers: "disabled";
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

export type UrimApiClient = {
  getHealth: () => Promise<HealthResponse>;
  getReadiness: () => Promise<ReadinessResponse>;
  getSystemAvailability: () => Promise<SystemAvailability>;
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

  return REQUIRED_DISABLED_DEPENDENCIES.every(
    (dependency) => dependencies[dependency] === "disabled"
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
