import type {
  DateWindow,
  IntegrationDecision,
  IsoDateTime,
  ObservationProvenance,
  ProviderCapability,
  ProviderHealth,
  ProviderResponse
} from "./common";

export type FootballFixtureStatus =
  | "SCHEDULED"
  | "POSTPONED"
  | "CANCELLED"
  | "IN_PLAY"
  | "FINISHED";

export type FootballMarket = "1X2" | "OVER_UNDER_2_5" | "BOTH_TEAMS_TO_SCORE";

export interface FootballTeamRef {
  team_id: string;
  name: string;
  country: string;
}

export interface FootballFixture {
  fixture_id: string;
  provider_event_id: string;
  competition: {
    competition_id: string;
    name: string;
    country: string;
  };
  season: string;
  kickoff_at: IsoDateTime;
  status: FootballFixtureStatus;
  home_team: FootballTeamRef;
  away_team: FootballTeamRef;
  venue: {
    name: string;
    city: string;
    country: string;
  };
  neutral_venue: boolean;
  provenance: ObservationProvenance;
}

export interface TeamStatisticsRequest {
  team_id: string;
  fixture_id?: string;
  as_of: IsoDateTime;
}

export interface TeamStatistics {
  team: FootballTeamRef;
  fixture_id?: string;
  as_of: IsoDateTime;
  scope: "PRE_MATCH";
  matches_included: number;
  matches_excluded: string[];
  rolling_window_label: string;
  metrics: {
    goals_for_avg: number;
    goals_against_avg: number;
    expected_goals_for_avg: number | null;
    expected_goals_against_avg: number | null;
    clean_sheet_rate: number;
    shots_for_avg: number;
    shots_against_avg: number;
  };
  provenance: ObservationProvenance;
}

export interface OddsValueRequest {
  fixture_id: string;
  market: FootballMarket;
  as_of: IsoDateTime;
}

export interface OddsBookmakerQuote {
  bookmaker: string;
  outcome: string;
  decimal_odds: number;
  observed_at: IsoDateTime;
  available_at: IsoDateTime;
}

export interface OddsValueSnapshot {
  odds_snapshot_id: string;
  fixture_id: string;
  market: FootballMarket;
  as_of: IsoDateTime;
  quotes: OddsBookmakerQuote[];
  implied_probabilities: Record<string, number>;
  value_assessment: {
    decision: IntegrationDecision;
    reasons: string[];
    edge: number | null;
  };
  provenance: ObservationProvenance;
}

export interface WeatherRequest {
  fixture_id: string;
  latitude: number;
  longitude: number;
  kickoff_at: IsoDateTime;
  as_of: IsoDateTime;
}

export interface WeatherObservation {
  fixture_id: string;
  coordinates: {
    latitude: number;
    longitude: number;
  };
  forecast_generated_at: IsoDateTime;
  valid_for: IsoDateTime;
  temperature_c: number | null;
  wind_kph: number | null;
  precipitation_mm: number | null;
  humidity_pct: number | null;
  condition: string;
  provenance: ObservationProvenance;
}

export interface MatchEventsNewsRequest {
  fixture_id: string;
  as_of: IsoDateTime;
}

export interface MatchEventNewsItem {
  item_id: string;
  fixture_id: string;
  phase: "PRE_MATCH";
  category: "TEAM_NEWS" | "INJURY" | "LINEUP_NOTE" | "MATCH_EVENT";
  title: string;
  summary: string;
  event_time: IsoDateTime | null;
  available_at: IsoDateTime;
  confidence: "LOW" | "MEDIUM" | "HIGH";
  provenance: ObservationProvenance;
}

export interface MatchEventsNewsSnapshot {
  fixture_id: string;
  as_of: IsoDateTime;
  items: MatchEventNewsItem[];
  provenance: ObservationProvenance;
}

export interface ExchangeRateRequest {
  base: "CDF" | "USD";
  quote: "CDF" | "USD";
  as_of: IsoDateTime;
}

export interface ExchangeRateSnapshot {
  rate_id: string;
  base: ExchangeRateRequest["base"];
  quote: ExchangeRateRequest["quote"];
  as_of: IsoDateTime;
  rate: number;
  display_only: true;
  provenance: ObservationProvenance;
}

interface UrimProviderBase {
  readonly product: "URIM";
  readonly provider: string;
  health(): Promise<ProviderHealth>;
  capabilities(): Promise<ProviderCapability[]>;
}

export interface SportsDataProvider extends UrimProviderBase {
  fetchFootballFixtures(window: DateWindow): Promise<ProviderResponse<FootballFixture[]>>;
  fetchTeamStatistics(request: TeamStatisticsRequest): Promise<ProviderResponse<TeamStatistics>>;
}

export interface OddsProvider extends UrimProviderBase {
  fetchOddsValue(request: OddsValueRequest): Promise<ProviderResponse<OddsValueSnapshot>>;
}

export interface WeatherProvider extends UrimProviderBase {
  fetchWeather(request: WeatherRequest): Promise<ProviderResponse<WeatherObservation>>;
}

export interface ExchangeRateProvider extends UrimProviderBase {
  fetchExchangeRate(request: ExchangeRateRequest): Promise<ProviderResponse<ExchangeRateSnapshot>>;
}

export interface NewsEventsProvider extends UrimProviderBase {
  fetchMatchEventsNews(
    request: MatchEventsNewsRequest
  ): Promise<ProviderResponse<MatchEventsNewsSnapshot>>;
}
