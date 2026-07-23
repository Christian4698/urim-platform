import assert from "node:assert/strict";
import test from "node:test";

import {
  ApiClientError,
  createApiClient,
  type FetchLike,
  type ReadinessResponse
} from "./api-client.ts";

const BASE_URL = "https://api.example.test";

const healthPayload = {
  status: "ok",
  app_name: "URIM",
  engine_name: "Kairos",
  phase: "phase-test"
} as const;

const readinessPayload: ReadinessResponse = {
  ready: true,
  phase: "phase-test",
  dependencies: {
    database: "ok",
    redis: "not_required",
    sports_providers: "disabled",
    bookmakers: "disabled",
    ml_models: "disabled",
    live: "disabled",
    real_betting: "disabled",
    prediction_creation: "disabled"
  }
};

const sportsProviderPayload = {
  provider: "api-football",
  status: "ready",
  enabled: true,
  configured: true,
  connected: true,
  last_success_at: "2026-07-23T10:00:00Z",
  quota_remaining_daily: 99,
  quota_remaining_minute: 9,
  priority_competition_count: 3,
  season: 2026,
  max_requests_per_sync: 10,
  prediction_creation_enabled: false,
  live_automatic_enabled: false,
  bookmakers_enabled: false,
  betting_enabled: false
} as const;

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    headers: { "Content-Type": "application/json" },
    status
  });
}

test("fetches health and readiness through the configured API base URL", async () => {
  const requestedUrls: string[] = [];
  const fetchImpl: FetchLike = async (input) => {
    const url = input.toString();
    requestedUrls.push(url);
    return url.endsWith("/health")
      ? jsonResponse(healthPayload)
      : jsonResponse(readinessPayload);
  };
  const client = createApiClient({ baseUrl: `${BASE_URL}/`, fetchImpl });

  const availability = await client.getSystemAvailability();

  assert.deepEqual(requestedUrls.sort(), [
    `${BASE_URL}/health`,
    `${BASE_URL}/readiness`
  ]);
  assert.deepEqual(availability, {
    api: "online",
    database: "available",
    service: "available",
    phase: "phase-test"
  });
});

test("reports a degraded service when PostgreSQL is unavailable", async () => {
  const unavailableReadiness: ReadinessResponse = {
    ...readinessPayload,
    ready: false,
    dependencies: { ...readinessPayload.dependencies, database: "unavailable" }
  };
  const fetchImpl: FetchLike = async (input) =>
    input.toString().endsWith("/health")
      ? jsonResponse(healthPayload)
      : jsonResponse(unavailableReadiness);
  const client = createApiClient({ baseUrl: BASE_URL, fetchImpl });

  assert.deepEqual(await client.getSystemAvailability(), {
    api: "online",
    database: "unavailable",
    service: "degraded",
    phase: "phase-test"
  });
});

test("reports a timeout without exposing the underlying error", async () => {
  const fetchImpl: FetchLike = (_input, init) =>
    new Promise((_resolve, reject) => {
      init?.signal?.addEventListener("abort", () => {
        reject(new Error("internal timeout detail"));
      });
    });
  const client = createApiClient({ baseUrl: BASE_URL, fetchImpl, timeoutMs: 5 });

  await assert.rejects(client.getHealth(), (error: unknown) => {
    assert.ok(error instanceof ApiClientError);
    assert.equal(error.code, "timeout");
    assert.doesNotMatch(error.message, /internal timeout detail/);
    return true;
  });
});

test("normalizes network failures to a public-safe error", async () => {
  const fetchImpl: FetchLike = async () => {
    throw new Error("password=DO_NOT_EXPOSE host=private-db.internal");
  };
  const client = createApiClient({ baseUrl: BASE_URL, fetchImpl });

  await assert.rejects(client.getHealth(), (error: unknown) => {
    assert.ok(error instanceof ApiClientError);
    assert.equal(error.code, "network");
    assert.doesNotMatch(error.message, /DO_NOT_EXPOSE|private-db/);
    return true;
  });
});

test("rejects invalid JSON responses", async () => {
  const fetchImpl: FetchLike = async () =>
    new Response("{invalid", {
      headers: { "Content-Type": "application/json" },
      status: 200
    });
  const client = createApiClient({ baseUrl: BASE_URL, fetchImpl });

  await assert.rejects(client.getHealth(), (error: unknown) => {
    assert.ok(error instanceof ApiClientError);
    assert.equal(error.code, "invalid_json");
    return true;
  });
});

test("rejects readiness responses that activate sensitive capabilities", async () => {
  const unsafeReadiness = {
    ...readinessPayload,
    dependencies: { ...readinessPayload.dependencies, live: "enabled" }
  };
  const fetchImpl: FetchLike = async () => jsonResponse(unsafeReadiness);
  const client = createApiClient({ baseUrl: BASE_URL, fetchImpl });

  await assert.rejects(client.getReadiness(), (error: unknown) => {
    assert.ok(error instanceof ApiClientError);
    assert.equal(error.code, "invalid_response");
    return true;
  });
});

test("rejects API URLs containing credentials", () => {
  assert.throws(
    () => createApiClient({ baseUrl: "https://user:secret@api.example.test" }),
    (error: unknown) => {
      assert.ok(error instanceof ApiClientError);
      assert.equal(error.code, "configuration");
      assert.doesNotMatch(error.message, /user|secret/);
      return true;
    }
  );
});

test("rejects a missing public API URL", () => {
  assert.throws(
    () => createApiClient({ baseUrl: " " }),
    (error: unknown) => {
      assert.ok(error instanceof ApiClientError);
      assert.equal(error.code, "configuration");
      return true;
    }
  );
});

test("rejects non-local HTTP API URLs", () => {
  assert.throws(
    () => createApiClient({ baseUrl: "http://api.example.test" }),
    (error: unknown) => {
      assert.ok(error instanceof ApiClientError);
      assert.equal(error.code, "configuration");
      return true;
    }
  );
});

test("accepts HTTP only for local development origins", async () => {
  const client = createApiClient({
    baseUrl: "http://localhost:8000",
    fetchImpl: async () => jsonResponse(healthPayload)
  });

  assert.deepEqual(await client.getHealth(), healthPayload);
});

test("rejects API origins containing a path, query or fragment", () => {
  for (const baseUrl of [
    "https://api.example.test/v1",
    "https://api.example.test?debug=true",
    "https://api.example.test#health"
  ]) {
    assert.throws(
      () => createApiClient({ baseUrl }),
      (error: unknown) => error instanceof ApiClientError && error.code === "configuration"
    );
  }
});

test("rejects successful responses with a non-JSON content type", async () => {
  const client = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async () =>
      new Response(JSON.stringify(healthPayload), {
        headers: { "Content-Type": "text/plain" },
        status: 200
      })
  });

  await assert.rejects(
    client.getHealth(),
    (error: unknown) => error instanceof ApiClientError && error.code === "invalid_response"
  );
});

test("rejects unbounded request timeouts", () => {
  assert.throws(
    () => createApiClient({ baseUrl: BASE_URL, timeoutMs: 30_001 }),
    (error: unknown) => error instanceof ApiClientError && error.code === "configuration"
  );
});

test("fetches the complete read-only sports data snapshot", async () => {
  const requestedPaths: string[] = [];
  const fetchImpl: FetchLike = async (input) => {
    const url = new URL(input.toString());
    requestedPaths.push(`${url.pathname}${url.search}`);
    if (url.pathname.endsWith("/provider")) {
      return jsonResponse(sportsProviderPayload);
    }
    if (url.pathname.endsWith("/competitions")) {
      return jsonResponse({
        items: [
          {
            provider_competition_id: 39,
            name: "Competition Test",
            kind: "League",
            country_name: "Test Country",
            current_season: 2026,
            fetched_at: "2026-07-23T10:00:00Z",
            freshness_status: "fresh"
          }
        ],
        count: 1,
        read_only: true
      });
    }
    if (url.pathname.endsWith("/matches/today")) {
      return jsonResponse({ items: [], count: 0, read_only: true });
    }
    if (url.pathname.endsWith("/matches/upcoming")) {
      return jsonResponse({
        items: [
          {
            provider_match_id: 10,
            kickoff_at: "2026-07-24T10:00:00Z",
            status_short: "NS",
            status_long: "Not Started",
            home_team_name: "Home Test",
            away_team_name: "Away Test",
            goals_home: null,
            goals_away: null,
            freshness_status: "fresh"
          }
        ],
        count: 1,
        read_only: true
      });
    }
    if (url.pathname.endsWith("/sync/status")) {
      return jsonResponse({
        provider: "api-football",
        latest: null,
        recent_errors: [],
        read_only: true
      });
    }
    return jsonResponse({
      as_of: "2026-07-23T10:00:00Z",
      threshold_minutes: 180,
      resources: [
        {
          resource: "matches",
          latest_fetched_at: null,
          age_minutes: null,
          status: "missing",
          row_count: 0
        }
      ],
      read_only: true
    });
  };

  const snapshot = await createApiClient({
    baseUrl: BASE_URL,
    fetchImpl
  }).getSportsData();

  assert.equal(snapshot.provider.status, "ready");
  assert.equal(snapshot.competitions.length, 1);
  assert.equal(snapshot.upcoming[0]?.provider_match_id, 10);
  assert.deepEqual(requestedPaths.sort(), [
    "/api/v1/sports/competitions",
    "/api/v1/sports/freshness",
    "/api/v1/sports/matches/today",
    "/api/v1/sports/matches/upcoming?days=7",
    "/api/v1/sports/provider",
    "/api/v1/sports/sync/status"
  ]);
});

test("rejects sports status that activates predictions or betting", async () => {
  const fetchImpl: FetchLike = async () =>
    jsonResponse({
      ...sportsProviderPayload,
      prediction_creation_enabled: true,
      betting_enabled: true
    });
  const client = createApiClient({ baseUrl: BASE_URL, fetchImpl });

  await assert.rejects(client.getSportsData(), (error: unknown) => {
    assert.ok(error instanceof ApiClientError);
    assert.equal(error.code, "invalid_response");
    return true;
  });
});
