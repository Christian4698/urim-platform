import { integrationProviders, integrationRuntimeConfig } from "./index";
import type {
  ExchangeRateSnapshot,
  FootballFixture,
  MatchEventsNewsSnapshot,
  OddsValueSnapshot,
  ProviderResponse
} from "./index";

type Assert<T extends true> = T;
type Extends<T, U> = T extends U ? true : false;

type UrimFixturesContract = Assert<
  Extends<
    Awaited<ReturnType<typeof integrationProviders.sportsData.fetchFootballFixtures>>,
    ProviderResponse<FootballFixture[]>
  >
>;

type UrimOddsContract = Assert<
  Extends<
    Awaited<ReturnType<typeof integrationProviders.odds.fetchOddsValue>>,
    ProviderResponse<OddsValueSnapshot>
  >
>;

type UrimExchangeRateContract = Assert<
  Extends<
    Awaited<ReturnType<typeof integrationProviders.exchangeRate.fetchExchangeRate>>,
    ProviderResponse<ExchangeRateSnapshot>
  >
>;

type UrimNewsEventsContract = Assert<
  Extends<
    Awaited<ReturnType<typeof integrationProviders.newsEvents.fetchMatchEventsNews>>,
    ProviderResponse<MatchEventsNewsSnapshot>
  >
>;

export type IntegrationContractTypeChecks = {
  fixtures: UrimFixturesContract;
  odds: UrimOddsContract;
  exchangeRate: UrimExchangeRateContract;
  newsEvents: UrimNewsEventsContract;
};

export const integrationSafetyTypeChecks = {
  live_enabled: integrationRuntimeConfig.live_enabled satisfies false,
  real_providers_enabled: integrationRuntimeConfig.real_providers_enabled satisfies false,
  external_api_calls_enabled: integrationRuntimeConfig.external_api_calls_enabled satisfies false
};
