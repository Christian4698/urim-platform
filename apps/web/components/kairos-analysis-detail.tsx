"use client";

import { useEffect, useState } from "react";
import {
  ApiClientError,
  createApiClient,
  type KairosAnalysis,
  type KairosSuggestionReason
} from "../lib/api-client";
import {
  KAIROS_ANALYTICAL_SUGGESTION_LABEL,
  KAIROS_GUARDRAIL_LABEL,
  presentKairosSuggestion
} from "../lib/kairos-presentation";
import { DataPanel, EmptyState, StatusBadge } from "./dashboard-ui";
import { Icon } from "./icon";

type ViewState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: KairosAnalysis };

export function KairosAnalysisDetail({
  providerMatchId,
  asOf
}: {
  providerMatchId: number;
  asOf: string;
}) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<ViewState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;
    createApiClient({ timeoutMs: 10_000 })
      .getKairosAnalysis(providerMatchId, asOf)
      .then((data) => {
        if (!cancelled) setState({ kind: "ready", data });
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setState({
            kind: "error",
            message:
              error instanceof ApiClientError
                ? error.message
                : "L’analyse Kairos est temporairement indisponible."
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [asOf, attempt, providerMatchId]);

  if (state.kind === "loading") {
    return <span aria-busy="true" className="skeleton-card kairos-detail-skeleton" />;
  }
  if (state.kind === "error") {
    return (
      <EmptyState description={state.message} title="Analyse indisponible">
        <button
          className="refresh-button"
          onClick={() => {
            setState({ kind: "loading" });
            setAttempt((current) => current + 1);
          }}
          type="button"
        >
          <Icon height={17} name="refresh" width={17} />
          Réessayer
        </button>
      </EmptyState>
    );
  }

  const { data } = state;
  const suggestion = data.analytical_suggestion;
  const presentation = presentKairosSuggestion(suggestion);
  const analyticalReasons = suggestion.reasons.filter(
    (reason) => reason.category === "analytical"
  );
  const guardrailReasons = [
    ...presentation.criticalGuardrails,
    ...presentation.otherGuardrails
  ];
  const positive = analyticalReasons.filter((reason) => reason.impact === "positive");
  const negative = analyticalReasons.filter((reason) => reason.impact === "negative");
  return (
    <div className="kairos-detail-content">
      <section className="kairos-detail-hero">
        <div>
          <span>{formatDateTime(data.kickoff_at)}</span>
          <h2>
            {suggestion.home_team_name} <small>contre</small>{" "}
            {suggestion.away_team_name}
          </h2>
        </div>
        <div className="kairos-detail-decision">
          <span>{KAIROS_ANALYTICAL_SUGGESTION_LABEL}</span>
          <strong>{suggestion.recommendation}</strong>
          <StatusBadge tone={suggestion.no_bet ? "warning" : "cyan"}>
            Score {suggestion.kairos_score.toFixed(1)} / 100
          </StatusBadge>
          <span>{KAIROS_GUARDRAIL_LABEL}</span>
          <StatusBadge tone="warning">{data.safety_decision}</StatusBadge>
          {presentation.hasStaleData && (
            <StatusBadge tone="warning">Données périmées</StatusBadge>
          )}
          {presentation.hasInsufficientData && (
            <StatusBadge tone="warning">Données insuffisantes</StatusBadge>
          )}
        </div>
      </section>

      <DataPanel
        description="Probabilités non calibrées issues d’une même distribution déterministe."
        title="Probabilités"
      >
        {data.probabilities ? (
          <div className="kairos-probability-grid">
            <Probability label="Domicile" value={data.probabilities.home_win} />
            <Probability label="Nul" value={data.probabilities.draw} />
            <Probability label="Extérieur" value={data.probabilities.away_win} />
          </div>
        ) : (
          <p className="sports-panel-empty">
            Données insuffisantes : le calcul probabiliste est bloqué sans
            valeur de remplacement.
          </p>
        )}
      </DataPanel>

      <section className="kairos-factor-grid">
        <FactorPanel factors={positive} positive title="Facteurs positifs" />
        <FactorPanel factors={negative} title="Facteurs négatifs" />
      </section>

      <DataPanel
        description="Facteurs calculés qui expliquent la suggestion sans la présenter comme une décision de pari."
        title="Raisons analytiques"
      >
        <ul className="kairos-decision-reasons">
          {analyticalReasons.map((reason) => (
            <li key={reason.code}>
              <StatusBadge
                tone={
                  reason.impact === "positive"
                    ? "success"
                    : reason.impact === "negative"
                      ? "warning"
                      : "neutral"
                }
              >
                {reason.code}
              </StatusBadge>
              <span>{reason.message}</span>
            </li>
          ))}
        </ul>
      </DataPanel>

      <DataPanel
        description="Limites et blocages pouvant imposer NO_BET ou INSUFFICIENT_DATA."
        title={KAIROS_GUARDRAIL_LABEL}
      >
        {guardrailReasons.length > 0 ? (
          <ul className="kairos-decision-reasons">
            {guardrailReasons.map((reason) => (
              <li key={reason.code}>
                <StatusBadge tone={reason.critical ? "warning" : "neutral"}>
                  {reason.code}
                </StatusBadge>
                <span>{reason.message}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="sports-panel-empty">
            NO_BET reste disponible comme garde-fou même sans avertissement
            critique.
          </p>
        )}
      </DataPanel>

      <div className="kairos-safety-note">
        <Icon height={20} name="shield" width={20} />
        <p>
          Lecture seule. Aucun bookmaker, aucune cote, aucune mise et aucune
          exécution automatique. Cette analyse ne promet aucun résultat.
        </p>
      </div>
    </div>
  );
}

function Probability({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{(value * 100).toFixed(1)}%</strong>
      <div className="kairos-score-track">
        <span style={{ width: `${value * 100}%` }} />
      </div>
    </div>
  );
}

function FactorPanel({
  title,
  factors,
  positive = false
}: {
  title: string;
  factors: KairosSuggestionReason[];
  positive?: boolean;
}) {
  return (
    <DataPanel className={positive ? "is-positive" : "is-negative"} title={title}>
      {factors.length ? (
        <ul className="kairos-reason-list">
          {factors.map((factor) => (
            <li className={positive ? "is-positive" : "is-negative"} key={factor.code}>
              {factor.message}
            </li>
          ))}
        </ul>
      ) : (
        <p className="sports-panel-empty">Aucun facteur de ce type disponible.</p>
      )}
    </DataPanel>
  );
}

function formatDateTime(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Horaire indisponible";
  return new Intl.DateTimeFormat("fr-CD", {
    dateStyle: "long",
    timeStyle: "short",
    timeZone: "Africa/Kinshasa"
  }).format(parsed);
}
