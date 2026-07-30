import assert from "node:assert/strict";
import test from "node:test";

import type {
  KairosSuggestion,
  KairosSuggestionReason
} from "./api-client.ts";
import {
  buildKairosAnalysisHref,
  getDailySuggestionsEmptyState,
  KAIROS_ANALYTICAL_SUGGESTION_LABEL,
  KAIROS_GUARDRAIL_LABEL,
  presentKairosSuggestion
} from "./kairos-presentation.ts";

function reason(
  code: string,
  category: "analytical" | "guardrail",
  critical = false
): KairosSuggestionReason {
  return {
    code,
    message: `Message public ${code}`,
    impact: category === "guardrail" ? "negative" : "positive",
    category,
    critical
  };
}

function suggestion(
  reasons: KairosSuggestionReason[],
  marketProbabilities: KairosSuggestion["market_probabilities"] = null
): KairosSuggestion {
  return {
    suggestion_version: "kairos_daily_suggestions_v1",
    provider_match_id: 999,
    kickoff_at: "2026-07-27T18:00:00Z",
    competition_name: "Competition Test",
    home_team_name: "Home Test",
    away_team_name: "Away Test",
    recommendation: "NO_BET",
    recommendation_code: "NO_BET",
    kairos_score: 0,
    confidence_level: "blocked",
    risk_level: "high",
    no_bet: true,
    reasons,
    market_probabilities: marketProbabilities,
    data_quality_score: 30,
    technical_confidence_score: 0,
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
  };
}

test("keeps NO_BET critical guardrails visible without the analytical top-three truncation", () => {
  const result = presentKairosSuggestion(
    suggestion([
      reason("NO_BET_HARD_BLOCK", "guardrail", true),
      reason("STALE_TARGET_DATA", "guardrail", true),
      reason("INSUFFICIENT_RESULT_HISTORY", "guardrail", true),
      reason("PROVENANCE_BLOCK", "guardrail", true),
      reason("ANALYTICAL_1", "analytical"),
      reason("ANALYTICAL_2", "analytical"),
      reason("ANALYTICAL_3", "analytical"),
      reason("ANALYTICAL_4", "analytical")
    ])
  );

  assert.equal(result.criticalGuardrails.length, 4);
  assert.equal(result.analyticalReasons.length, 3);
  assert.equal(result.hasStaleData, true);
  assert.equal(result.hasInsufficientData, true);
});

test("identifies stale and insufficient data as separate release-critical states", () => {
  const stale = presentKairosSuggestion(
    suggestion([reason("STALE_TARGET_DATA", "guardrail", true)], {
      home_win: 0.5,
      draw: 0.3,
      away_win: 0.2,
      home_or_draw: 0.8,
      away_or_draw: 0.5,
      home_or_away: 0.7,
      over_2_5: 0.55,
      under_2_5: 0.45,
      btts: 0.5
    })
  );
  const insufficient = presentKairosSuggestion(
    suggestion([
      reason("INSUFFICIENT_RESULT_HISTORY", "guardrail", true)
    ])
  );

  assert.equal(stale.hasStaleData, true);
  assert.equal(stale.hasInsufficientData, false);
  assert.equal(insufficient.hasStaleData, false);
  assert.equal(insufficient.hasInsufficientData, true);
});

test("presents absence of matches without inventing a suggestion", () => {
  const empty = getDailySuggestionsEmptyState({
    local_date: "2026-07-27",
    suggestions: []
  });

  assert.equal(empty?.title, "Aucune suggestion disponible");
  assert.match(empty?.description ?? "", /Aucun match synchronisé/);
  assert.equal(
    getDailySuggestionsEmptyState({
      local_date: "2026-07-27",
      suggestions: [suggestion([])]
    }),
    null
  );
});

test("preserves the exact daily as_of in the detailed analysis link", () => {
  const asOf = "2026-07-27T12:00:00+00:00";

  assert.deepEqual(buildKairosAnalysisHref(suggestion([]), asOf), {
    pathname: "/kairos-analysis/999",
    query: { as_of: asOf }
  });
});

test("preserves the consulted business date in the detailed analysis link", () => {
  const asOf = "2026-07-30T18:00:00+00:00";

  assert.deepEqual(
    buildKairosAnalysisHref(suggestion([]), asOf, "2026-07-31"),
    {
      pathname: "/kairos-analysis/999",
      query: { as_of: asOf, date: "2026-07-31" }
    }
  );
});

test("uses distinct guardrail and analytical suggestion labels", () => {
  assert.equal(KAIROS_GUARDRAIL_LABEL, "Garde-fou Kairos");
  assert.equal(
    KAIROS_ANALYTICAL_SUGGESTION_LABEL,
    "Suggestion analytique"
  );
  assert.notEqual(KAIROS_GUARDRAIL_LABEL, KAIROS_ANALYTICAL_SUGGESTION_LABEL);
});
