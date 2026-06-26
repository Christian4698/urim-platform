export const appConfig = Object.freeze({
  appName: process.env.APP_NAME ?? "URIM",
  engineName: process.env.ENGINE_NAME ?? "Kairos",
  appVersion: process.env.APP_VERSION ?? "0.1.0",
  defaultLocale: process.env.DEFAULT_LOCALE ?? "fr-CD",
  defaultCurrency: process.env.DEFAULT_CURRENCY ?? "CDF",
  enableLive: process.env.ENABLE_LIVE === "true",
  enableRealBetting: process.env.ENABLE_REAL_BETTING === "true",
  allowProductionMocks: process.env.ALLOW_PRODUCTION_MOCKS === "true"
});

export function formatCurrency(
  value: number,
  locale = appConfig.defaultLocale,
  currency = appConfig.defaultCurrency
) {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    maximumFractionDigits: 0
  }).format(value);
}
