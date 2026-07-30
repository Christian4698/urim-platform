import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

const webRoot = process.cwd();
const repoRoot = resolve(webRoot, "../..");

function read(relativePath: string): string {
  return readFileSync(resolve(repoRoot, relativePath), "utf8");
}

test("ships every required Programme A route and runtime state", () => {
  const requiredFiles = [
    "apps/web/app/page.tsx",
    "apps/web/app/dashboard/page.tsx",
    "apps/web/app/donnees-sportives/page.tsx",
    "apps/web/app/suggestions/page.tsx",
    "apps/web/app/opportunities/page.tsx",
    "apps/web/app/kairos/performance/page.tsx",
    "apps/web/app/kairos-analysis/[providerMatchId]/page.tsx",
    "apps/web/app/disponibilite/page.tsx",
    "apps/web/app/modules/page.tsx",
    "apps/web/app/parametres/page.tsx",
    "apps/web/app/loading.tsx",
    "apps/web/app/error.tsx",
    "apps/web/app/not-found.tsx"
  ];

  for (const relativePath of requiredFiles) {
    assert.doesNotThrow(() => read(relativePath), `${relativePath} must exist`);
  }
});

test("Kairos B2.4 Opportunity Center is read-only and exposes explicit gates", () => {
  const source = [
    read("apps/web/app/opportunities/page.tsx"),
    read("apps/web/components/kairos-opportunities.tsx"),
    read("apps/web/lib/api-client.ts")
  ].join("\n");

  assert.match(source, /≥ 70|estimated_probability/);
  assert.match(source, /NO_BET/);
  assert.match(source, /Lecture seule|read_only/);
  assert.match(source, /Aucun pari|not_for_betting/);
  assert.doesNotMatch(
    source,
    /API_FOOTBALL_KEY|x-apisports-key|DATABASE_URL|stake|bookmaker_id/
  );
});

test("Kairos B2.4.1 explains empty states and separates estimated from observed performance", () => {
  const source = [
    read("apps/web/components/kairos-opportunities.tsx"),
    read("apps/web/components/kairos-performance.tsx"),
    read("apps/web/components/kairos-analysis-detail.tsx"),
    read("apps/web/app/kairos/performance/page.tsx"),
    read("apps/web/lib/api-client.ts")
  ].join("\n");

  assert.match(source, /Zéro\s+opportunité n’est pas une panne/);
  assert.match(source, /Principales catégories de rejet/);
  assert.match(source, /Échantillon insuffisant/);
  assert.match(source, /probabilité estimée|probabilités estimées/i);
  assert.match(source, /taux observé/i);
  assert.match(source, /VOID/);
  assert.match(source, /Sans échantillon/);
  assert.doesNotMatch(
    source,
    /API_FOOTBALL_KEY|x-apisports-key|DATABASE_URL|bookmaker_id|stake_suggestion/
  );
});

test("Kairos B2.4.2 navigates one Kinshasa business date at a time", () => {
  const businessTime = read("apps/web/lib/business-time.ts");
  const navigation = read(
    "apps/web/components/kairos-date-navigation.tsx"
  );
  const apiClient = read("apps/web/lib/api-client.ts");
  const datedViews = [
    read("apps/web/components/kairos-suggestions.tsx"),
    read("apps/web/components/kairos-opportunities.tsx")
  ].join("\n");

  assert.match(navigation, /Aujourd’hui/);
  assert.match(navigation, /Demain/);
  assert.match(navigation, /Prochains 7 jours/);
  assert.match(navigation, /Date consultée/);
  assert.match(navigation, /Heure locale/);
  assert.match(apiClient, /kairos\/suggestions\?\$\{query\.toString\(\)\}/);
  assert.match(apiClient, /kairos\/opportunities\?\$\{query\.toString\(\)\}/);
  assert.match(apiClient, /response\.local_date !== requestedDate/);
  assert.match(apiClient, /isInstantOnBusinessDate/);
  assert.match(datedViews, /competition_name/);
  assert.doesNotMatch(datedViews, /Compétition\s+\$\{|bookmaker|cote|mise/i);
  assert.equal(
    (businessTime.match(/Africa\/Kinshasa/g) ?? []).length,
    1
  );
});

test("Kairos B2.2 UI remains read-only and contains no bookmaker or secret integration", () => {
  const source = [
    read("apps/web/components/kairos-suggestions.tsx"),
    read("apps/web/components/kairos-analysis-detail.tsx"),
    read("apps/web/lib/api-client.ts")
  ].join("\n");

  assert.match(source, /Lecture seule|read_only/);
  assert.match(source, /not_for_betting|Aucun bookmaker/);
  assert.doesNotMatch(
    source,
    /API_FOOTBALL_KEY|x-apisports-key|v3\.football\.api-sports\.io|DATABASE_URL/
  );
});

test("Kairos B2.2 product states and labels are truthful across the interface", () => {
  const source = [
    read("apps/web/app/page.tsx"),
    read("apps/web/app/dashboard/page.tsx"),
    read("apps/web/app/donnees-sportives/page.tsx"),
    read("apps/web/app/modules/page.tsx"),
    read("apps/web/components/sports-data-overview.tsx"),
    read("apps/web/components/kairos-suggestions.tsx"),
    read("apps/web/components/kairos-analysis-detail.tsx"),
    read("apps/web/lib/kairos-presentation.ts")
  ].join("\n");

  assert.match(source, /Bêta analytique|bêta analytique/);
  assert.match(source, /Garde-fou Kairos/);
  assert.match(source, /Suggestion analytique/);
  assert.match(source, /Données périmées/);
  assert.match(source, /Données insuffisantes/);
  assert.match(source, /Aucun pari réel|Aucun pari/);
  assert.doesNotMatch(
    source,
    /Kairos désactivé|Intelligence prédictive[\s\S]{0,80}Désactivée|Kairos ne consomme aucun|Prédiction désactivée|Décision analytique/
  );
});

test("frontend environment example exposes only approved public origins", () => {
  const variableNames = read("apps/web/.env.example")
    .split(/\r?\n/)
    .filter((line) => line && !line.startsWith("#"))
    .map((line) => line.split("=", 1)[0])
    .sort();

  assert.deepEqual(variableNames, ["NEXT_PUBLIC_API_URL", "NEXT_PUBLIC_SITE_URL"]);
  assert.doesNotMatch(variableNames.join("\n"), /DATABASE|PASSWORD|SECRET|TOKEN|PROVIDER/);
});

test("Render Blueprint deploys the Next.js web service without secrets", () => {
  const blueprint = read("render.yaml");

  assert.match(blueprint, /name: urim-web/);
  assert.match(blueprint, /runtime: node/);
  assert.match(blueprint, /pnpm install --frozen-lockfile --prod=false/);
  assert.match(blueprint, /pnpm web:build/);
  assert.match(blueprint, /NEXT_PUBLIC_API_URL/);
  assert.match(blueprint, /- urim\.pro/);
  assert.doesNotMatch(blueprint, /DATABASE_URL|API_KEY|PASSWORD|SECRET/);
});

test("sensitive runtime capabilities remain disabled in committed configuration", () => {
  const environment = read(".env.example");

  assert.match(environment, /ENABLE_LIVE=false/);
  assert.match(environment, /ENABLE_REAL_BETTING=false/);
  assert.match(environment, /ALLOW_PRODUCTION_MOCKS=false/);
  assert.doesNotMatch(environment, /ENABLE_LIVE=true|ENABLE_REAL_BETTING=true/);
});

test("sports data UI is read-only and contains no provider secret surface", () => {
  const source = [
    read("apps/web/components/sports-data-overview.tsx"),
    read("apps/web/app/donnees-sportives/page.tsx"),
    read("apps/web/lib/api-client.ts"),
    read("apps/web/.env.example")
  ].join("\n");

  assert.match(source, /Lecture seule|read-only/);
  assert.match(source, /Kairos · bêta analytique|prediction_creation_enabled/);
  assert.doesNotMatch(
    source,
    /API_FOOTBALL_KEY|x-apisports-key|v3\.football\.api-sports\.io/
  );
});
