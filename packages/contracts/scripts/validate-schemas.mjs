import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const currentDir = dirname(fileURLToPath(import.meta.url));
const schemaDir = join(currentDir, "..", "schemas");
const files = readdirSync(schemaDir).filter((file) => file.endsWith(".json"));
const requiredKeys = ["$schema", "title", "type"];

let failures = 0;

for (const file of files) {
  const fullPath = join(schemaDir, file);
  let parsed;

  try {
    parsed = JSON.parse(readFileSync(fullPath, "utf8"));
  } catch (error) {
    failures += 1;
    console.error(`${file}: invalid JSON`);
    console.error(error);
    continue;
  }

  for (const key of requiredKeys) {
    if (!(key in parsed)) {
      failures += 1;
      console.error(`${file}: missing top-level ${key}`);
    }
  }

  if (parsed.$schema !== "https://json-schema.org/draft/2020-12/schema") {
    failures += 1;
    console.error(`${file}: expected JSON Schema draft 2020-12`);
  }
}

if (failures > 0) {
  process.exitCode = 1;
} else {
  console.log(`Validated ${files.length} URIM contract schemas.`);
}
