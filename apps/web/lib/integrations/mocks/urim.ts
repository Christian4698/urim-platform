import type {
  ExchangeRateSnapshot,
  FootballFixture,
  MatchEventsNewsSnapshot,
  OddsValueSnapshot,
  ProviderCapability,
  SportsDataProvider,
  TeamStatistics,
  WeatherObservation,
  OddsProvider,
  WeatherProvider,
  ExchangeRateProvider,
  NewsEventsProvider
} from "../types";
import { createMockHealth, createMockProvenance, createMockResponse } from "./helpers";

const SPORTS_MOCK_PROVIDER = "urim-sports-data-mock-provider";
const ODDS_MOCK_PROVIDER = "urim-odds-mock-provider";
const WEATHER_MOCK_PROVIDER = "urim-weather-mock-provider";
const EXCHANGE_RATE_MOCK_PROVIDER = "urim-exchange-rate-mock-provider";
const NEWS_EVENTS_MOCK_PROVIDER = "urim-news-events-mock-provider";

const FIXTURE_EVENT_ID = "mock-football-fixture-001";
const HOME_TEAM_ID = "mock-team-kinshasa-01";
const AWAY_TEAM_ID = "mock-team-lemba-02";

const sportsCapabilities: ProviderCapability[] = ["football-fixtures", "team-statistics"];
const oddsCapabilities: ProviderCapability[] = ["odds-value"];
const weatherCapabilities: ProviderCapability[] = ["weather"];
const exchangeRateCapabilities: ProviderCapability[] = ["exchange-rate"];
const newsEventsCapabilities: ProviderCapability[] = ["match-news-events"];

function createFixture(): FootballFixture {
  return {
    fixture_id: FIXTURE_EVENT_ID,
    provider_event_id: FIXTURE_EVENT_ID,
    competition: {
      competition_id: "mock-competition-urim-demo",
      name: "URIM Demo League",
      country: "CD"
    },
    season: "2026",
    kickoff_at: "2026-07-12T18:00:00.000Z",
    status: "SCHEDULED",
    home_team: {
      team_id: HOME_TEAM_ID,
      name: "Kinshasa Demo FC",
      country: "CD"
    },
    away_team: {
      team_id: AWAY_TEAM_ID,
      name: "Lemba Demo United",
      country: "CD"
    },
    venue: {
      name: "Demo Stadium",
      city: "Kinshasa",
      country: "CD"
    },
    neutral_venue: false,
    provenance: createMockProvenance({
      provider: SPORTS_MOCK_PROVIDER,
      provider_event_id: FIXTURE_EVENT_ID
    })
  };
}

function createTeamStatistics(team_id: string, fixture_id: string | undefined, as_of: string): TeamStatistics {
  const isAway = team_id === AWAY_TEAM_ID;
  const providerEventId = `mock-team-statistics:${team_id}`;

  return {
    team: {
      team_id,
      name: isAway ? "Lemba Demo United" : "Kinshasa Demo FC",
      country: "CD"
    },
    fixture_id,
    as_of,
    scope: "PRE_MATCH",
    matches_included: 10,
    matches_excluded: fixture_id ? [fixture_id] : [],
    rolling_window_label: "last_10_completed_matches_excluding_target",
    metrics: {
      goals_for_avg: isAway ? 1.1 : 1.4,
      goals_against_avg: isAway ? 1.2 : 0.9,
      expected_goals_for_avg: null,
      expected_goals_against_avg: null,
      clean_sheet_rate: isAway ? 0.2 : 0.4,
      shots_for_avg: isAway ? 9.2 : 11.8,
      shots_against_avg: isAway ? 10.4 : 8.7
    },
    provenance: createMockProvenance({
      provider: SPORTS_MOCK_PROVIDER,
      provider_event_id: providerEventId,
      raw_hash_seed: `${providerEventId}:${as_of}:${fixture_id ?? "no-fixture"}`
    })
  };
}

function createOddsSnapshot(
  fixture_id: string,
  market: OddsValueSnapshot["market"],
  as_of: string
): OddsValueSnapshot {
  const providerEventId = `mock-odds:${fixture_id}:${market}`;

  return {
    odds_snapshot_id: `mock-odds-snapshot:${fixture_id}:${market}:${as_of}`,
    fixture_id,
    market,
    as_of,
    quotes: [
      {
        bookmaker: "MockBook A",
        outcome: "HOME",
        decimal_odds: 2.2,
        observed_at: "2026-07-05T11:50:00.000Z",
        available_at: "2026-07-05T11:52:00.000Z"
      },
      {
        bookmaker: "MockBook A",
        outcome: "DRAW",
        decimal_odds: 3.1,
        observed_at: "2026-07-05T11:50:00.000Z",
        available_at: "2026-07-05T11:52:00.000Z"
      },
      {
        bookmaker: "MockBook A",
        outcome: "AWAY",
        decimal_odds: 3.4,
        observed_at: "2026-07-05T11:50:00.000Z",
        available_at: "2026-07-05T11:52:00.000Z"
      }
    ],
    implied_probabilities: {
      HOME: 0.432,
      DRAW: 0.307,
      AWAY: 0.28
    },
    value_assessment: {
      decision: "NO_BET",
      reasons: [
        "Mock odds only.",
        "No calibrated model probability is attached to this scaffold.",
        "LIVE OFF and betting disabled."
      ],
      edge: null
    },
    provenance: createMockProvenance({
      provider: ODDS_MOCK_PROVIDER,
      provider_event_id: providerEventId,
      raw_hash_seed: `${providerEventId}:${as_of}`
    })
  };
}

function createWeather(
  fixture_id: string,
  latitude: number,
  longitude: number,
  kickoff_at: string
): WeatherObservation {
  const providerEventId = `mock-weather:${fixture_id}`;

  return {
    fixture_id,
    coordinates: {
      latitude,
      longitude
    },
    forecast_generated_at: "2026-07-05T10:00:00.000Z",
    valid_for: kickoff_at,
    temperature_c: 27,
    wind_kph: 8,
    precipitation_mm: 0.2,
    humidity_pct: 68,
    condition: "Mock partly cloudy forecast",
    provenance: createMockProvenance({
      provider: WEATHER_MOCK_PROVIDER,
      provider_event_id: providerEventId,
      raw_hash_seed: `${providerEventId}:${latitude}:${longitude}:${kickoff_at}`
    })
  };
}

function createExchangeRate(base: "CDF" | "USD", quote: "CDF" | "USD", as_of: string): ExchangeRateSnapshot {
  const providerEventId = `mock-exchange-rate:${base}:${quote}`;
  const rate = base === "USD" && quote === "CDF" ? 2850 : 1 / 2850;

  return {
    rate_id: `mock-fx-rate:${base}:${quote}:${as_of}`,
    base,
    quote,
    as_of,
    rate,
    display_only: true,
    provenance: createMockProvenance({
      provider: EXCHANGE_RATE_MOCK_PROVIDER,
      provider_event_id: providerEventId,
      raw_hash_seed: `${providerEventId}:${as_of}`
    })
  };
}

function createEventsNews(fixture_id: string, as_of: string): MatchEventsNewsSnapshot {
  const providerEventId = `mock-events-news:${fixture_id}`;

  return {
    fixture_id,
    as_of,
    items: [
      {
        item_id: "mock-news-001",
        fixture_id,
        phase: "PRE_MATCH",
        category: "TEAM_NEWS",
        title: "Mock training note",
        summary: "Demo-only note used to exercise news ingestion without external calls.",
        event_time: null,
        available_at: "2026-07-05T09:45:00.000Z",
        confidence: "MEDIUM",
        provenance: createMockProvenance({
          provider: NEWS_EVENTS_MOCK_PROVIDER,
          provider_event_id: "mock-news-001"
        })
      },
      {
        item_id: "mock-lineup-note-001",
        fixture_id,
        phase: "PRE_MATCH",
        category: "LINEUP_NOTE",
        title: "Mock probable lineup caveat",
        summary: "Probable lineup is explicitly not treated as official.",
        event_time: null,
        available_at: "2026-07-05T10:20:00.000Z",
        confidence: "LOW",
        provenance: createMockProvenance({
          provider: NEWS_EVENTS_MOCK_PROVIDER,
          provider_event_id: "mock-lineup-note-001",
          quality_flags: ["MISSING_EXPLICIT"]
        })
      }
    ],
    provenance: createMockProvenance({
      provider: NEWS_EVENTS_MOCK_PROVIDER,
      provider_event_id: providerEventId,
      raw_hash_seed: `${providerEventId}:${as_of}`
    })
  };
}

export const mockSportsDataProvider: SportsDataProvider = {
  product: "URIM",
  provider: SPORTS_MOCK_PROVIDER,
  async health() {
    return createMockHealth({
      product: "URIM",
      provider: SPORTS_MOCK_PROVIDER,
      capabilities: sportsCapabilities
    });
  },
  async capabilities() {
    return sportsCapabilities;
  },
  async fetchFootballFixtures(window) {
    const data = [createFixture()].filter(
      (fixture) => fixture.kickoff_at >= window.from && fixture.kickoff_at <= window.to
    );

    return createMockResponse({
      provider: SPORTS_MOCK_PROVIDER,
      provider_event_id: "mock-football-fixtures-window",
      request_id: `mock-request:fixtures:${window.from}:${window.to}:${window.as_of ?? "no-as-of"}`,
      data,
      warnings: ["Demo fixture data only; do not use as actual coverage."]
    });
  },
  async fetchTeamStatistics(request) {
    const data = createTeamStatistics(request.team_id, request.fixture_id, request.as_of);

    return createMockResponse({
      provider: SPORTS_MOCK_PROVIDER,
      provider_event_id: data.provenance.provider_event_id,
      request_id: `mock-request:team-statistics:${request.team_id}:${request.as_of}`,
      data,
      warnings: ["Statistics exclude the target fixture when fixture_id is provided."]
    });
  }
};

export const mockOddsProvider: OddsProvider = {
  product: "URIM",
  provider: ODDS_MOCK_PROVIDER,
  async health() {
    return createMockHealth({
      product: "URIM",
      provider: ODDS_MOCK_PROVIDER,
      capabilities: oddsCapabilities
    });
  },
  async capabilities() {
    return oddsCapabilities;
  },
  async fetchOddsValue(request) {
    const data = createOddsSnapshot(request.fixture_id, request.market, request.as_of);

    return createMockResponse({
      provider: ODDS_MOCK_PROVIDER,
      provider_event_id: data.provenance.provider_event_id,
      request_id: `mock-request:odds:${request.fixture_id}:${request.market}:${request.as_of}`,
      data,
      warnings: ["NO_BET by design: no calibrated edge is produced by mock odds."]
    });
  }
};

export const mockWeatherProvider: WeatherProvider = {
  product: "URIM",
  provider: WEATHER_MOCK_PROVIDER,
  async health() {
    return createMockHealth({
      product: "URIM",
      provider: WEATHER_MOCK_PROVIDER,
      capabilities: weatherCapabilities
    });
  },
  async capabilities() {
    return weatherCapabilities;
  },
  async fetchWeather(request) {
    const data = createWeather(
      request.fixture_id,
      request.latitude,
      request.longitude,
      request.kickoff_at
    );

    return createMockResponse({
      provider: WEATHER_MOCK_PROVIDER,
      provider_event_id: data.provenance.provider_event_id,
      request_id: `mock-request:weather:${request.fixture_id}:${request.as_of}`,
      data
    });
  }
};

export const mockExchangeRateProvider: ExchangeRateProvider = {
  product: "URIM",
  provider: EXCHANGE_RATE_MOCK_PROVIDER,
  async health() {
    return createMockHealth({
      product: "URIM",
      provider: EXCHANGE_RATE_MOCK_PROVIDER,
      capabilities: exchangeRateCapabilities
    });
  },
  async capabilities() {
    return exchangeRateCapabilities;
  },
  async fetchExchangeRate(request) {
    const data = createExchangeRate(request.base, request.quote, request.as_of);

    return createMockResponse({
      provider: EXCHANGE_RATE_MOCK_PROVIDER,
      provider_event_id: data.provenance.provider_event_id,
      request_id: `mock-request:exchange-rate:${request.base}:${request.quote}:${request.as_of}`,
      data,
      warnings: ["Display-only mock FX data; not used for betting execution."]
    });
  }
};

export const mockNewsEventsProvider: NewsEventsProvider = {
  product: "URIM",
  provider: NEWS_EVENTS_MOCK_PROVIDER,
  async health() {
    return createMockHealth({
      product: "URIM",
      provider: NEWS_EVENTS_MOCK_PROVIDER,
      capabilities: newsEventsCapabilities
    });
  },
  async capabilities() {
    return newsEventsCapabilities;
  },
  async fetchMatchEventsNews(request) {
    const data = createEventsNews(request.fixture_id, request.as_of);

    return createMockResponse({
      provider: NEWS_EVENTS_MOCK_PROVIDER,
      provider_event_id: data.provenance.provider_event_id,
      request_id: `mock-request:events-news:${request.fixture_id}:${request.as_of}`,
      data,
      warnings: ["Pre-match mock news only; not mixed with live or post-match metrics."]
    });
  }
};
