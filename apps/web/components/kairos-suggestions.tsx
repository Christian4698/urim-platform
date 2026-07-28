"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ApiClientError,
  createApiClient,
  type KairosDailySuggestions,
  type KairosSuggestion
} from "../lib/api-client";
import {
  buildKairosAnalysisHref,
  getDailySuggestionsEmptyState,
  KAIROS_ANALYTICAL_SUGGESTION_LABEL,
  KAIROS_GUARDRAIL_LABEL,
  presentKairosSuggestion
} from "../lib/kairos-presentation";
import { EmptyState, StatusBadge } from "./dashboard-ui";
import { Icon } from "./icon";

type ViewState =
  | { kind: "loading" }
  | { kind: "offline" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: KairosDailySuggestions };

export function KairosSuggestions() {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<ViewState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (!navigator.onLine) {
        setState({ kind: "offline" });
        return;
      }
      setState({ kind: "loading" });
      try {
        const data = await createApiClient({ timeoutMs: 10_000 }).getDailySuggestions();
        if (!cancelled) {
          setState({ kind: "ready", data });
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            kind: "error",
            message:
              error instanceof ApiClientError
                ? error.message
                : "Les suggestions Kairos sont temporairement indisponibles."
          });
        }
      }
    };
    const handleOffline = () => setState({ kind: "offline" });
    const handleOnline = () => setAttempt((current) => current + 1);
    window.addEventListener("offline", handleOffline);
    window.addEventListener("online", handleOnline);
    void load();
    return () => {
      cancelled = true;
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("online", handleOnline);
    };
  }, [attempt]);

  if (state.kind === "loading") {
    return (
      <section aria-busy="true" aria-label="Chargement des suggestions Kairos">
        <div className="kairos-card-grid">
          {Array.from({ length: 3 }, (_, index) => (
            <span className="skeleton-card kairos-card-skeleton" key={index} />
          ))}
        </div>
      </section>
    );
  }

  if (state.kind === "offline" || state.kind === "error") {
    return (
      <EmptyState
        description={
          state.kind === "offline"
            ? "Kairos ne réutilise pas une ancienne suggestion comme si elle était à jour."
            : state.message
        }
        title={state.kind === "offline" ? "Mode hors ligne" : "Lecture impossible"}
      >
        <button
          className="refresh-button"
          onClick={() => setAttempt((current) => current + 1)}
          type="button"
        >
          <Icon height={17} name="refresh" width={17} />
          Réessayer
        </button>
      </EmptyState>
    );
  }

  const emptyState = getDailySuggestionsEmptyState(state.data);
  if (emptyState) {
    return (
      <EmptyState
        description={emptyState.description}
        title={emptyState.title}
      />
    );
  }

  return (
    <div className="kairos-suggestions-content">
      <div className="kairos-day-summary">
        <span>
          {state.data.suggestion_count} suggestion(s) sur{" "}
          {state.data.evaluated_match_count} match(s) analysé(s)
        </span>
        <span>Calcul arrêté au {formatDateTime(state.data.as_of)}</span>
      </div>
      <section className="kairos-card-grid" aria-label="Suggestions Kairos du jour">
        {state.data.suggestions.map((suggestion) => (
          <SuggestionCard
            asOf={state.data.as_of}
            key={suggestion.provider_match_id}
            suggestion={suggestion}
          />
        ))}
      </section>
      <div className="kairos-safety-note">
        <Icon height={20} name="shield" width={20} />
        <p>{state.data.warnings[0]}</p>
      </div>
    </div>
  );
}

function SuggestionCard({
  suggestion,
  asOf
}: {
  suggestion: KairosSuggestion;
  asOf: string;
}) {
  const presentation = presentKairosSuggestion(suggestion);
  return (
    <article className={suggestion.no_bet ? "kairos-card is-no-bet" : "kairos-card"}>
      <div className="kairos-card-topline">
        <time dateTime={suggestion.kickoff_at}>{formatDateTime(suggestion.kickoff_at)}</time>
        <StatusBadge tone={suggestion.no_bet ? "warning" : "cyan"}>
          {suggestion.no_bet
            ? `${KAIROS_GUARDRAIL_LABEL} · NO_BET`
            : `Score ${suggestion.kairos_score.toFixed(1)}`}
        </StatusBadge>
      </div>
      <div className="kairos-fixture">
        <strong>{suggestion.home_team_name}</strong>
        <span>contre</span>
        <strong>{suggestion.away_team_name}</strong>
      </div>
      <div className="kairos-recommendation">
        <span>{KAIROS_ANALYTICAL_SUGGESTION_LABEL}</span>
        <h2>{recommendationLabel(suggestion)}</h2>
      </div>
      <div className="kairos-score-track" aria-label={`Score Kairos ${suggestion.kairos_score}`}>
        <span style={{ width: `${suggestion.kairos_score}%` }} />
      </div>
      <div className="kairos-badges">
        <StatusBadge tone="info">Confiance {suggestion.confidence_level}</StatusBadge>
        <StatusBadge tone="warning">Risque {suggestion.risk_level}</StatusBadge>
        <StatusBadge tone="neutral">Qualité {suggestion.data_quality_score.toFixed(0)}</StatusBadge>
        {presentation.hasStaleData && (
          <StatusBadge tone="warning">Données périmées</StatusBadge>
        )}
        {presentation.hasInsufficientData && (
          <StatusBadge tone="warning">Données insuffisantes</StatusBadge>
        )}
      </div>
      {presentation.criticalGuardrails.length > 0 && (
        <section className="kairos-card-reason-group is-guardrail">
          <strong>{KAIROS_GUARDRAIL_LABEL}</strong>
          <ul className="kairos-reason-list">
            {presentation.criticalGuardrails.map((reason) => (
              <li className="is-negative" key={reason.code}>
                {reason.message}
              </li>
            ))}
          </ul>
        </section>
      )}
      {presentation.analyticalReasons.length > 0 && (
        <section className="kairos-card-reason-group">
          <strong>Raisons analytiques</strong>
          <ul className="kairos-reason-list">
            {presentation.analyticalReasons.map((reason) => (
              <li className={`is-${reason.impact}`} key={reason.code}>
                {reason.message}
              </li>
            ))}
          </ul>
        </section>
      )}
      <Link
        className="action-link action-link-secondary"
        href={buildKairosAnalysisHref(suggestion, asOf)}
      >
        <span>Voir l’analyse complète</span>
        <Icon height={17} name="arrow" width={17} />
      </Link>
    </article>
  );
}

function recommendationLabel(suggestion: KairosSuggestion): string {
  const doubleChanceLabels: Record<string, string> = {
    HOME_OR_DRAW: "Double Chance · domicile ou nul",
    AWAY_OR_DRAW: "Double Chance · extérieur ou nul",
    HOME_OR_AWAY: "Double Chance · sans nul"
  };
  return doubleChanceLabels[suggestion.recommendation_code] ?? suggestion.recommendation;
}

function formatDateTime(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Horaire indisponible";
  }
  return new Intl.DateTimeFormat("fr-CD", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Africa/Kinshasa"
  }).format(parsed);
}
