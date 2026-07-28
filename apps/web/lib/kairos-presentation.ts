import type {
  KairosDailySuggestions,
  KairosSuggestion,
  KairosSuggestionReason
} from "./api-client";

export const KAIROS_GUARDRAIL_LABEL = "Garde-fou Kairos";
export const KAIROS_ANALYTICAL_SUGGESTION_LABEL = "Suggestion analytique";

const INSUFFICIENT_DATA_CODES = new Set([
  "INSUFFICIENT_RESULT_HISTORY",
  "RESULT_SAMPLE_BELOW_MINIMUM"
]);

export type KairosSuggestionPresentation = {
  hasStaleData: boolean;
  hasInsufficientData: boolean;
  criticalGuardrails: KairosSuggestionReason[];
  otherGuardrails: KairosSuggestionReason[];
  analyticalReasons: KairosSuggestionReason[];
};

export function presentKairosSuggestion(
  suggestion: KairosSuggestion
): KairosSuggestionPresentation {
  const hasStaleData = suggestion.reasons.some(
    (reason) => reason.code === "STALE_TARGET_DATA"
  );
  const hasInsufficientData =
    suggestion.no_bet &&
    (suggestion.market_probabilities === null ||
      suggestion.reasons.some((reason) =>
        INSUFFICIENT_DATA_CODES.has(reason.code)
      ));
  const criticalGuardrails = suggestion.reasons.filter(
    (reason) => reason.category === "guardrail" && reason.critical
  );
  const otherGuardrails = suggestion.reasons.filter(
    (reason) => reason.category === "guardrail" && !reason.critical
  );
  const analyticalReasons = suggestion.reasons
    .filter(
      (reason) =>
        reason.category === "analytical" && reason.impact !== "neutral"
    )
    .slice(0, 3);

  return {
    hasStaleData,
    hasInsufficientData,
    criticalGuardrails,
    otherGuardrails,
    analyticalReasons
  };
}

export function buildKairosAnalysisHref(
  suggestion: Pick<KairosSuggestion, "provider_match_id">,
  asOf: string
) {
  return {
    pathname: `/kairos-analysis/${suggestion.provider_match_id}`,
    query: { as_of: asOf }
  };
}

export function getDailySuggestionsEmptyState(
  data: Pick<KairosDailySuggestions, "suggestions">
) {
  if (data.suggestions.length > 0) {
    return null;
  }
  return {
    title: "Aucune suggestion disponible",
    description:
      "Aucun match futur synchronisé aujourd’hui ne possède actuellement un contexte exploitable. Aucune valeur par défaut n’est affichée."
  } as const;
}
