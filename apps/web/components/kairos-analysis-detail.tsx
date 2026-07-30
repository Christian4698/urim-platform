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
import { formatBusinessDateTime } from "../lib/business-time";
import {
  ActionLink,
  DataPanel,
  EmptyState,
  StatusBadge
} from "./dashboard-ui";
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
  const rejectionReasons = detailRejectionReasons(data);
  const missingData = Object.entries(data.data_availability)
    .filter(([, availability]) => !availability.available_for_both_teams)
    .map(([feature]) => missingFeatureLabel(feature));
  return (
    <div className="kairos-detail-content">
      <section className="kairos-detail-hero">
        <div>
          <span>
            {formatBusinessDateTime(data.kickoff_at, "long") ??
              "Horaire indisponible"}
          </span>
          {suggestion.competition_name !== null && (
            <span className="kairos-competition">
              {suggestion.competition_name}
            </span>
          )}
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
        description="Raisons analytiques sûres ayant conduit au refus ou à la prudence."
        title="Pourquoi cette décision ?"
      >
        {rejectionReasons.length ? (
          <ul className="kairos-decision-reasons">
            {rejectionReasons.map((reason) => (
              <li key={reason.code}>
                <StatusBadge tone="warning">{reason.code}</StatusBadge>
                <span>{reason.message}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="sports-panel-empty">
            Aucun motif de rejet supplémentaire n’est associé à cette analyse.
          </p>
        )}
        {missingData.length > 0 && (
          <p className="kairos-missing-data">
            Données manquantes ou insuffisantes : {missingData.join(", ")}.
          </p>
        )}
      </DataPanel>

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

      <DataPanel
        description="Deux notions volontairement séparées."
        title="Estimation et performance historique"
      >
        <div className="kairos-estimation-history">
          <p>
            Les pourcentages affichés sur ce match sont des estimations
            pré-match non calibrées. Ils ne constituent pas un taux de réussite
            observé.
          </p>
          <p>
            La performance historique utilise uniquement les résolutions
            SUCCESS et FAILURE du journal immuable ; VOID et non-résolus sont
            exclus.
          </p>
          <ActionLink href="/kairos/performance" variant="secondary">
            Consulter le rapport de performance
          </ActionLink>
        </div>
      </DataPanel>

      <DataPanel
        description="Estimations dédiées aux deux périodes. Les scores HT manquants restent absents et bloquent le calcul."
        title="Analyse mi-temps B2.4"
      >
        {data.half_time_analysis?.length ? (
          <div className="kairos-probability-grid">
            {data.half_time_analysis.map((market) => (
              <div key={market.market}>
                <span>{halfTimeMarketLabel(market.market)}</span>
                <strong>
                  {market.estimated_probability === null
                    ? "Insuffisant"
                    : `${(market.estimated_probability * 100).toFixed(1)}%`}
                </strong>
                <small>
                  n={market.sample_size} · qualité{" "}
                  {market.data_quality_score.toFixed(0)} · technique{" "}
                  {market.technical_confidence_score.toFixed(0)}
                </small>
              </div>
            ))}
          </div>
        ) : (
          <p className="sports-panel-empty">
            Aucune observation HT/FT exploitable n’est disponible pour cette
            analyse.
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

function detailRejectionReasons(data: KairosAnalysis) {
  const reasons: Array<{ code: string; message: string }> = [];
  if (data.safety_decision === "INSUFFICIENT_DATA") {
    const halfTimeDataIsInsufficient =
      data.half_time_analysis?.some((market) => market.insufficient_data) ?? false;
    reasons.push(
      halfTimeDataIsInsufficient
        ? {
            code: "insufficient_half_time_data",
            message:
              "L’historique mi-temps exploitable est insuffisant ; aucune valeur n’est imputée."
          }
        : {
            code: "provider_data_partial",
            message:
              "Les données analytiques disponibles sont partielles ; aucune valeur n’est imputée."
          }
    );
  }
  if (data.data_freshness.status === "stale") {
    reasons.push({
      code: "stale_data",
      message: "Les données disponibles dépassent le seuil de fraîcheur."
    });
  }
  if (data.data_quality_score < 65) {
    reasons.push({
      code: "low_data_quality",
      message: "La qualité des données reste sous le gate B2.4."
    });
  }
  if (data.confidence_score < 50) {
    reasons.push({
      code: "low_technical_confidence",
      message: "La confiance technique reste sous le gate B2.4."
    });
  }
  if (data.warnings.some((warning) => warning.severity === "blocking")) {
    reasons.push({
      code: "critical_guardrail",
      message: "Un garde-fou critique impose le refus de publication."
    });
  }
  if (data.suggestion.no_bet && reasons.length === 0) {
    reasons.push({
      code: "estimated_probability_below_threshold",
      message: "Aucun signal ne franchit simultanément tous les seuils requis."
    });
  }
  return reasons;
}

function missingFeatureLabel(feature: string): string {
  const labels: Record<string, string> = {
    recent_results: "résultats récents",
    venue_results: "résultats domicile/extérieur",
    standings: "classement",
    shots: "tirs",
    possession: "possession",
    corners: "corners",
    cards: "cartons"
  };
  return labels[feature] ?? "donnée analytique requise";
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

function halfTimeMarketLabel(market: string): string {
  const labels: Record<string, string> = {
    FIRST_HALF_MORE_GOALS: "Plus de buts en 1re période",
    SECOND_HALF_MORE_GOALS: "Plus de buts en 2de période",
    EQUAL_HALF_GOALS: "Buts égaux par période",
    FIRST_HALF_OVER_0_5: "1re période · au moins un but",
    SECOND_HALF_OVER_0_5: "2de période · au moins un but",
    SECOND_HALF_OVER_1_5: "2de période · au moins deux buts"
  };
  return labels[market] ?? market;
}
