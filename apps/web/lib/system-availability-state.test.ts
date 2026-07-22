import assert from "node:assert/strict";
import test from "node:test";

import { getSystemAvailabilityPresentation } from "./system-availability-state.ts";

test("presents a loading state", () => {
  const presentation = getSystemAvailabilityPresentation({ kind: "loading" });

  assert.equal(presentation.api.value, "Vérification");
  assert.equal(presentation.database.value, "Vérification");
});

test("presents API online and database available", () => {
  const presentation = getSystemAvailabilityPresentation({
    kind: "loaded",
    availability: {
      api: "online",
      database: "available",
      service: "available",
      phase: "phase-test"
    }
  });

  assert.equal(presentation.api.value, "En ligne");
  assert.equal(presentation.database.value, "Disponible");
  assert.equal(presentation.service.value, "Opérationnel");
});

test("presents a degraded service when the database is unavailable", () => {
  const presentation = getSystemAvailabilityPresentation({
    kind: "loaded",
    availability: {
      api: "online",
      database: "unavailable",
      service: "degraded",
      phase: "phase-test"
    }
  });

  assert.equal(presentation.api.value, "En ligne");
  assert.equal(presentation.database.value, "Indisponible");
  assert.equal(presentation.service.value, "Dégradé");
});

test("presents a service unavailable state after client errors", () => {
  const presentation = getSystemAvailabilityPresentation({ kind: "error" });

  assert.equal(presentation.api.value, "Indisponible");
  assert.equal(presentation.database.value, "Inconnue");
  assert.equal(presentation.service.value, "Service indisponible");
});

test("presents a distinct offline state without inventing database availability", () => {
  const presentation = getSystemAvailabilityPresentation({ kind: "offline" });

  assert.equal(presentation.api.value, "Hors ligne");
  assert.equal(presentation.database.value, "Non vérifiée");
  assert.equal(presentation.service.value, "Mode hors ligne");
});
