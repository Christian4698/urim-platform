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
    redis: "ok",
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

const marketProbabilities = {
  home_win: 0.55,
  draw: 0.25,
  away_win: 0.2,
  home_or_draw: 0.8,
  away_or_draw: 0.45,
  home_or_away: 0.75,
  over_2_5: 0.6,
  under_2_5: 0.4,
  btts: 0.52
} as const;

const kairosSuggestionPayload = {
  suggestion_version: "kairos_daily_suggestions_v1",
  provider_match_id: 999,
  kickoff_at: "2026-07-27T18:00:00Z",
  competition_name: "Competition Test",
  home_team_name: "Home Test",
  away_team_name: "Away Test",
  recommendation: "Home Win",
  recommendation_code: "HOME_WIN",
  kairos_score: 60,
  confidence_level: "medium",
  risk_level: "elevated",
  no_bet: false,
  reasons: [
    {
      code: "RECENT_FORM",
      message: "Forme récente favorable à domicile.",
      impact: "positive",
      category: "analytical",
      critical: false
    }
  ],
  market_probabilities: marketProbabilities,
  data_quality_score: 80,
  technical_confidence_score: 55,
  feature_snapshot_hash: "a".repeat(64),
  decision_hash: "b".repeat(64),
  analysis_path: "/api/v1/kairos/matches/999/analysis",
  read_only: true,
  persisted: false,
  provider_calls: false,
  bookmaker_data_used: false,
  automatic_betting_enabled: false,
  live_automatic_enabled: false,
  not_for_betting: true
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

test("fetches safe daily Kairos suggestions from the URIM API", async () => {
  const fetchImpl: FetchLike = async (input) => {
    assert.equal(
      new URL(input.toString()).pathname,
      "/api/v1/kairos/suggestions/today"
    );
    return jsonResponse({
      local_date: "2026-07-27",
      timezone: "Africa/Kinshasa",
      as_of: "2026-07-27T12:00:00Z",
      suggestion_count: 1,
      evaluated_match_count: 1,
      skipped_unsafe_match_count: 0,
      suggestions: [kairosSuggestionPayload],
      warnings: ["Analyse non calibrée."],
      read_only: true,
      db_writes: false,
      provider_calls: false,
      automatic_betting_enabled: false,
      live_automatic_enabled: false,
      not_for_betting: true
    });
  };

  const result = await createApiClient({
    baseUrl: BASE_URL,
    fetchImpl
  }).getDailySuggestions();

  assert.equal(result.suggestions[0]?.recommendation, "Home Win");
  assert.equal(result.suggestions[0]?.bookmaker_data_used, false);
});

test("fetches one explicit Kinshasa suggestion date without mixing days", async () => {
  const requestedUrls: URL[] = [];
  const payload = {
    local_date: "2026-07-31",
    timezone: "Africa/Kinshasa",
    as_of: "2026-07-30T18:00:00Z",
    suggestion_count: 1,
    evaluated_match_count: 1,
    skipped_unsafe_match_count: 0,
    suggestions: [
      {
        ...kairosSuggestionPayload,
        kickoff_at: "2026-07-31T18:00:00Z"
      }
    ],
    warnings: ["Analyse non calibrée."],
    read_only: true,
    db_writes: false,
    provider_calls: false,
    automatic_betting_enabled: false,
    live_automatic_enabled: false,
    not_for_betting: true
  } as const;
  const client = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async (input) => {
      requestedUrls.push(new URL(input.toString()));
      return jsonResponse(payload);
    }
  });

  const result = await client.getSuggestionsForDate("2026-07-31");

  assert.equal(requestedUrls[0]?.pathname, "/api/v1/kairos/suggestions");
  assert.equal(requestedUrls[0]?.searchParams.get("date"), "2026-07-31");
  assert.equal(result.local_date, "2026-07-31");
  assert.equal(result.suggestions[0]?.competition_name, "Competition Test");

  let fetchCalled = false;
  const invalidDateClient = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async () => {
      fetchCalled = true;
      return jsonResponse(payload);
    }
  });
  await assert.rejects(
    invalidDateClient.getSuggestionsForDate("2026-07-31T00:00:00Z"),
    (error: unknown) =>
      error instanceof ApiClientError && error.code === "configuration"
  );
  assert.equal(fetchCalled, false);

  const mismatchedDateClient = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async () =>
      jsonResponse({ ...payload, local_date: "2026-07-30" })
  });
  await assert.rejects(
    mismatchedDateClient.getSuggestionsForDate("2026-07-31"),
    (error: unknown) =>
      error instanceof ApiClientError && error.code === "invalid_response"
  );

  const crossDayKickoffClient = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async () =>
      jsonResponse({
        ...payload,
        suggestions: [
          {
            ...payload.suggestions[0],
            kickoff_at: "2026-07-30T22:59:59Z"
          }
        ]
      })
  });
  await assert.rejects(
    crossDayKickoffClient.getSuggestionsForDate("2026-07-31"),
    (error: unknown) =>
      error instanceof ApiClientError && error.code === "invalid_response"
  );
});

test("fetches strictly gated Kairos opportunities", async () => {
  const candidate = {
    market: "SECOND_HALF_OVER_0_5",
    estimated_probability: 0.8,
    data_quality_score: 80,
    technical_confidence_score: 60,
    sample_size: 10,
    risk: "guarded",
    reasons: ["Historique HT/FT complet."],
    guardrails: [],
    eligible_for_opportunity: true,
    analysis_hash: "c".repeat(64)
  };
  const halfTimeAnalysis = {
    model_version: "kairos_half_time_b2_4_v1",
    ...candidate,
    h2h_sample_size: 3,
    insufficient_data: false
  };
  const evaluatedMatch = {
    provider_match_id: 999,
    kickoff_at: "2026-07-28T18:00:00Z",
    competition_name: "Competition Test",
    home_team_name: "Home Test",
    away_team_name: "Away Test",
    section: "GOAL_MARKETS",
    safety_decision: "ANALYSIS_ALLOWED",
    primary_analysis: candidate,
    alternative_analyses: [],
    evaluated_markets: [halfTimeAnalysis],
    rejection_reasons: [],
    missing_data: [],
    data_freshness: "fresh",
    read_only: true,
    persisted_by_request: false,
    not_for_betting: true
  };
  const payload = {
    local_date: "2026-07-28",
    timezone: "Africa/Kinshasa",
    as_of: "2026-07-28T12:00:00Z",
    generated_at: "2026-07-28T12:00:00Z",
    opportunity_count: 1,
    evaluated_match_count: 1,
    skipped_unsafe_match_count: 0,
    watchlist_count: 0,
    no_bet_count: 0,
    insufficient_data_count: 0,
    stale_data_count: 0,
    rejection_reason_counts: {},
    message_code: "opportunities_available",
    message: "Une opportunité analytique disponible, sous garde-fous.",
    data_freshness: {
      status: "fresh",
      fresh_match_count: 1,
      stale_match_count: 0,
      partial_match_count: 0
    },
    opportunities: [evaluatedMatch],
    evaluated_matches: [evaluatedMatch],
    warnings: ["Analyse non calibrée."],
    thresholds: {
      estimated_probability: 0.7,
      data_quality_score: 65,
      technical_confidence_score: 50
    },
    calibration_status: "not_calibrated",
    resolved_journal_sample_size: 0,
    observed_hit_rate: null,
    resolved_metrics_by_market: {},
    read_only: true,
    db_writes: false,
    provider_calls: false,
    automatic_betting_enabled: false,
    live_automatic_enabled: false,
    not_for_betting: true
  };
  const fetchImpl: FetchLike = async (input) => {
    assert.equal(
      new URL(input.toString()).pathname,
      "/api/v1/kairos/opportunities/today"
    );
    return jsonResponse(payload);
  };

  const result = await createApiClient({
    baseUrl: BASE_URL,
    fetchImpl
  }).getDailyOpportunities();

  assert.equal(
    result.opportunities[0]?.primary_analysis?.estimated_probability,
    0.8
  );
  assert.equal(result.observed_hit_rate, null);
  assert.equal(
    result.opportunities[0]?.competition_name,
    "Competition Test"
  );

  const datedMatch = {
    ...evaluatedMatch,
    kickoff_at: "2026-07-31T18:00:00Z"
  };
  const datedPayload = {
    ...payload,
    local_date: "2026-07-31",
    opportunities: [datedMatch],
    evaluated_matches: [datedMatch]
  };
  const datedClient = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async (input) => {
      const url = new URL(input.toString());
      assert.equal(url.pathname, "/api/v1/kairos/opportunities");
      assert.equal(url.searchParams.get("date"), "2026-07-31");
      return jsonResponse(datedPayload);
    }
  });
  assert.equal(
    (await datedClient.getOpportunitiesForDate("2026-07-31")).local_date,
    "2026-07-31"
  );

  const crossDateMatch = {
    ...evaluatedMatch,
    kickoff_at: "2026-07-30T23:00:00Z"
  };
  const crossDateClient = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async () =>
      jsonResponse({
        ...payload,
        local_date: "2026-07-30",
        opportunities: [crossDateMatch],
        evaluated_matches: [crossDateMatch]
      })
  });
  await assert.rejects(
    crossDateClient.getOpportunitiesForDate("2026-07-30"),
    (error: unknown) =>
      error instanceof ApiClientError && error.code === "invalid_response"
  );

  const correlatedPayload = {
    ...payload,
    opportunities: [
      {
        ...payload.opportunities[0],
        alternative_analyses: [
          {
            ...candidate,
            market: "SECOND_HALF_OVER_1_5"
          }
        ]
      }
    ]
  };
  const correlatedClient = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async () => jsonResponse(correlatedPayload)
  });
  await assert.rejects(
    correlatedClient.getDailyOpportunities(),
    (error: unknown) =>
      error instanceof ApiClientError && error.code === "invalid_response"
  );
});

test("rejects an opportunity below a centralized threshold", async () => {
  const client = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async () =>
      jsonResponse({
        local_date: "2026-07-28",
        timezone: "Africa/Kinshasa",
        as_of: "2026-07-28T12:00:00Z",
        opportunity_count: 1,
        evaluated_match_count: 1,
        opportunities: [
          {
            provider_match_id: 999,
            kickoff_at: "2026-07-28T18:00:00Z",
            home_team_name: "Home Test",
            away_team_name: "Away Test",
            section: "GOAL_MARKETS",
            safety_decision: "ANALYSIS_ALLOWED",
            primary_analysis: {
              market: "SECOND_HALF_OVER_0_5",
              estimated_probability: 0.69,
              data_quality_score: 80,
              technical_confidence_score: 60,
              sample_size: 10,
              risk: "guarded",
              reasons: ["Test."],
              guardrails: [],
              eligible_for_opportunity: true,
              analysis_hash: "c".repeat(64)
            },
            alternative_analyses: [],
            evaluated_markets: [],
            read_only: true,
            persisted_by_request: false,
            not_for_betting: true
          }
        ],
        warnings: [],
        thresholds: {
          estimated_probability: 0.7,
          data_quality_score: 65,
          technical_confidence_score: 50
        },
        calibration_status: "not_calibrated",
        resolved_journal_sample_size: 0,
        observed_hit_rate: null,
        resolved_metrics_by_market: {},
        read_only: true,
        db_writes: false,
        provider_calls: false,
        automatic_betting_enabled: false,
        live_automatic_enabled: false,
        not_for_betting: true
      })
  });

  await assert.rejects(
    client.getDailyOpportunities(),
    (error: unknown) =>
      error instanceof ApiClientError && error.code === "invalid_response"
  );
});

test("validates an empty then populated Kairos performance report", async () => {
  const marketKeys = [
    "FIRST_HALF_MORE_GOALS",
    "SECOND_HALF_MORE_GOALS",
    "EQUAL_HALF_GOALS",
    "FIRST_HALF_OVER_0_5",
    "SECOND_HALF_OVER_0_5",
    "SECOND_HALF_OVER_1_5",
    "HOME_OR_DRAW",
    "AWAY_OR_DRAW",
    "HOME_OR_AWAY"
  ];
  const emptySegment = (key: string) => ({
    key,
    label: key,
    total_snapshots: 0,
    resolved_sample_size: 0,
    success_count: 0,
    void_count: 0,
    unresolved_count: 0,
    observed_hit_rate: null,
    estimated_probability_mean: null,
    sample_status: "no_sample"
  });
  const emptyReport = {
    generated_at: "2026-07-30T12:00:00Z",
    total_snapshots: 0,
    resolved: 0,
    unresolved: 0,
    void: 0,
    resolved_sample_size: 0,
    success_count: 0,
    observed_hit_rate: null,
    sample_status: "no_sample",
    performance_by_market: marketKeys.map(emptySegment),
    performance_by_competition: [],
    performance_by_probability_band: [],
    performance_by_quality_level: [],
    calibration_buckets: [],
    last_resolution_at: null,
    last_report_generated_at: "2026-07-30T12:00:00Z",
    warnings: ["Échantillon insuffisant."],
    calibration_status: "not_calibrated",
    read_only: true,
    db_writes: false,
    provider_calls: false,
    automatic_betting_enabled: false,
    not_for_betting: true
  };
  const emptyClient = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async (input) => {
      assert.equal(
        new URL(input.toString()).pathname,
        "/api/v1/kairos/performance"
      );
      return jsonResponse(emptyReport);
    }
  });
  assert.equal((await emptyClient.getKairosPerformance()).sample_status, "no_sample");

  const populatedSegment = {
    key: "SECOND_HALF_OVER_0_5",
    label: "Seconde période · au moins un but",
    total_snapshots: 32,
    resolved_sample_size: 30,
    success_count: 21,
    void_count: 1,
    unresolved_count: 1,
    observed_hit_rate: 0.7,
    estimated_probability_mean: 0.76,
    sample_status: "descriptive_sample_available"
  };
  const populatedReport = {
    ...emptyReport,
    total_snapshots: 32,
    resolved: 30,
    unresolved: 1,
    void: 1,
    resolved_sample_size: 30,
    success_count: 21,
    observed_hit_rate: 0.7,
    sample_status: "descriptive_sample_available",
    performance_by_market: marketKeys.map((key) =>
      key === populatedSegment.key ? populatedSegment : emptySegment(key)
    ),
    performance_by_competition: [populatedSegment],
    performance_by_probability_band: [populatedSegment],
    performance_by_quality_level: [populatedSegment],
    calibration_buckets: [populatedSegment],
    last_resolution_at: "2026-07-30T11:00:00Z"
  };
  const populatedClient = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async () => jsonResponse(populatedReport)
  });
  const performance = await populatedClient.getKairosPerformance();
  assert.equal(performance.resolved_sample_size, 30);
  assert.equal(performance.observed_hit_rate, 0.7);
  assert.equal(performance.void, 1);
  assert.equal(performance.unresolved, 1);
});

test("rejects a Kairos payload that activates betting", async () => {
  const client = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async () =>
      jsonResponse({
        local_date: "2026-07-27",
        timezone: "Africa/Kinshasa",
        as_of: "2026-07-27T12:00:00Z",
        suggestion_count: 1,
        evaluated_match_count: 1,
        skipped_unsafe_match_count: 0,
        suggestions: [
          { ...kairosSuggestionPayload, automatic_betting_enabled: true }
        ],
        warnings: [],
        read_only: true,
        db_writes: false,
        provider_calls: false,
        automatic_betting_enabled: false,
        live_automatic_enabled: false,
        not_for_betting: true
      })
  });

  await assert.rejects(
    client.getDailySuggestions(),
    (error: unknown) =>
      error instanceof ApiClientError && error.code === "invalid_response"
  );
});

test("rejects inconsistent daily suggestion counters", async () => {
  const client = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async () =>
      jsonResponse({
        local_date: "2026-07-27",
        timezone: "Africa/Kinshasa",
        as_of: "2026-07-27T12:00:00Z",
        suggestion_count: 1,
        evaluated_match_count: 0,
        skipped_unsafe_match_count: 16,
        suggestions: [kairosSuggestionPayload],
        warnings: [],
        read_only: true,
        db_writes: false,
        provider_calls: false,
        automatic_betting_enabled: false,
        live_automatic_enabled: false,
        not_for_betting: true
      })
  });

  await assert.rejects(
    client.getDailySuggestions(),
    (error: unknown) =>
      error instanceof ApiClientError && error.code === "invalid_response"
  );
});

test("fetches a complete Kairos analysis and validates its match id", async () => {
  const requestedAsOf = "2026-07-27T12:00:00Z";
  const payload = {
    provider_match_id: 999,
    kickoff_at: "2026-07-27T18:00:00Z",
    model_version: "kairos_core_b2_2_v1",
    prediction_time: requestedAsOf,
    probabilities: { home_win: 0.55, draw: 0.25, away_win: 0.2 },
    market_probabilities: marketProbabilities,
    confidence_score: 55,
    data_quality_score: 80,
    reasons: [],
    warnings: [],
    data_freshness: {
      as_of: requestedAsOf,
      max_available_at: "2026-07-27T11:55:00Z",
      target_fetched_at: "2026-07-27T11:56:00Z",
      target_age_minutes: 4,
      status: "fresh",
      threshold_minutes: 180
    },
    data_availability: {},
    safety_decision: "NO_BET",
    decision: "NO_BET",
    analytical_suggestion: kairosSuggestionPayload,
    suggestion: kairosSuggestionPayload,
    analysis_status: "ready",
    read_only: true,
    persisted: false,
    official_prediction_published: false,
    automatic_betting_enabled: false,
    live_automatic_enabled: false,
    not_for_betting: true
  };
  const fetchImpl: FetchLike = async (input) => {
    const url = new URL(input.toString());
    assert.equal(url.pathname, "/api/v1/kairos/matches/999/analysis");
    assert.equal(url.searchParams.get("as_of"), requestedAsOf);
    return jsonResponse(payload);
  };
  const client = createApiClient({ baseUrl: BASE_URL, fetchImpl });

  const analysis = await client.getKairosAnalysis(999, requestedAsOf);
  assert.equal(analysis.provider_match_id, 999);
  assert.equal(analysis.safety_decision, "NO_BET");
  assert.equal(analysis.analytical_suggestion.recommendation, "Home Win");
  await assert.rejects(
    client.getKairosAnalysis(Number.MAX_SAFE_INTEGER + 1),
    (error: unknown) =>
      error instanceof ApiClientError && error.code === "configuration"
  );

  const invalidHalfTimeClient = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async () =>
      jsonResponse({ ...payload, half_time_analysis: "untrusted" })
  });
  await assert.rejects(
    invalidHalfTimeClient.getKairosAnalysis(999),
    (error: unknown) =>
      error instanceof ApiClientError && error.code === "invalid_response"
  );
});

test("rejects inconsistent Kairos probability shapes", async () => {
  const requestedAsOf = "2026-07-27T12:00:00Z";
  const client = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async () =>
      jsonResponse({
        provider_match_id: 999,
        kickoff_at: "2026-07-27T18:00:00Z",
        model_version: "kairos_core_b2_2_v1",
        prediction_time: requestedAsOf,
        probabilities: null,
        market_probabilities: marketProbabilities,
        confidence_score: 0,
        data_quality_score: 30,
        reasons: [],
        warnings: [],
        safety_decision: "INSUFFICIENT_DATA",
        decision: "INSUFFICIENT_DATA",
        analytical_suggestion: {
          ...kairosSuggestionPayload,
          recommendation: "NO_BET",
          recommendation_code: "NO_BET",
          no_bet: true
        },
        suggestion: {
          ...kairosSuggestionPayload,
          recommendation: "NO_BET",
          recommendation_code: "NO_BET",
          no_bet: true
        },
        analysis_status: "insufficient_data",
        read_only: true,
        persisted: false,
        official_prediction_published: false,
        automatic_betting_enabled: false,
        live_automatic_enabled: false,
        not_for_betting: true
      })
  });

  await assert.rejects(
    client.getKairosAnalysis(999, requestedAsOf),
    (error: unknown) =>
      error instanceof ApiClientError && error.code === "invalid_response"
  );
});

test("maps Redis rate-limit unavailability to a public-safe frontend error", async () => {
  const client = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async () =>
      jsonResponse(
        {
          detail: {
            code: "kairos_rate_limit_unavailable",
            message: "private redis host and credentials"
          }
        },
        503
      )
  });

  await assert.rejects(client.getDailySuggestions(), (error: unknown) => {
    assert.ok(error instanceof ApiClientError);
    assert.equal(error.code, "rate_limit_unavailable");
    assert.equal(error.status, 503);
    assert.match(error.message, /contrôle de débit Redis est indisponible/);
    assert.doesNotMatch(error.message, /private|credentials|host/);
    return true;
  });
});

test("maps a missing match to an explicit public-safe error", async () => {
  const client = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async () =>
      jsonResponse(
        {
          detail: {
            code: "kairos_match_not_found_as_of",
            message: "internal match lookup detail"
          }
        },
        404
      )
  });

  await assert.rejects(
    client.getKairosAnalysis(999, "2026-07-27T12:00:00Z"),
    (error: unknown) => {
      assert.ok(error instanceof ApiClientError);
      assert.equal(error.code, "not_found");
      assert.match(error.message, /Aucun match n’est disponible/);
      assert.doesNotMatch(error.message, /internal|lookup/);
      return true;
    }
  );
});

test("rejects an analysis returned for a different as_of", async () => {
  const client = createApiClient({
    baseUrl: BASE_URL,
    fetchImpl: async () =>
      jsonResponse({
        provider_match_id: 999,
        kickoff_at: "2026-07-27T18:00:00Z",
        model_version: "kairos_core_b2_2_v1",
        prediction_time: "2026-07-27T11:59:59Z",
        probabilities: { home_win: 0.55, draw: 0.25, away_win: 0.2 },
        market_probabilities: marketProbabilities,
        confidence_score: 55,
        data_quality_score: 80,
        reasons: [],
        warnings: [],
        safety_decision: "NO_BET",
        decision: "NO_BET",
        analytical_suggestion: kairosSuggestionPayload,
        suggestion: kairosSuggestionPayload,
        analysis_status: "ready",
        read_only: true,
        persisted: false,
        official_prediction_published: false,
        automatic_betting_enabled: false,
        live_automatic_enabled: false,
        not_for_betting: true
      })
  });

  await assert.rejects(
    client.getKairosAnalysis(999, "2026-07-27T12:00:00Z"),
    (error: unknown) =>
      error instanceof ApiClientError && error.code === "invalid_response"
  );
});
