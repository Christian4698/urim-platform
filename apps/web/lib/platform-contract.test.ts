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
