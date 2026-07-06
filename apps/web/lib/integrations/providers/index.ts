import {
  assertMockOnlyIntegrationConfig,
  integrationRuntimeConfig,
  type IntegrationRuntimeConfig
} from "../config";
import {
  mockExchangeRateProvider,
  mockNewsEventsProvider,
  mockOddsProvider,
  mockSportsDataProvider,
  mockWeatherProvider
} from "../mocks";
import type {
  ExchangeRateProvider,
  NewsEventsProvider,
  OddsProvider,
  SportsDataProvider,
  WeatherProvider
} from "../types";

export interface IntegrationProviderRegistry {
  config: IntegrationRuntimeConfig;
  sportsData: SportsDataProvider;
  odds: OddsProvider;
  weather: WeatherProvider;
  exchangeRate: ExchangeRateProvider;
  newsEvents: NewsEventsProvider;
}

export function createIntegrationProviders(
  config: IntegrationRuntimeConfig = integrationRuntimeConfig
): IntegrationProviderRegistry {
  assertMockOnlyIntegrationConfig(config);

  return Object.freeze({
    config,
    sportsData: mockSportsDataProvider,
    odds: mockOddsProvider,
    weather: mockWeatherProvider,
    exchangeRate: mockExchangeRateProvider,
    newsEvents: mockNewsEventsProvider
  });
}

export const integrationProviders = createIntegrationProviders();
