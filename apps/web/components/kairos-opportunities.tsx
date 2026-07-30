"use client";

import { useEffect, useState } from "react";
import {
  ApiClientError,
  createApiClient,
  type KairosDailyOpportunities,
  type KairosMatchOpportunity,
  type KairosOpportunityCandidate
} from "../lib/api-client";
import { EmptyState, StatusBadge } from "./dashboard-ui";
import { Icon } from "./icon";

type ViewState =
  | { kind: "loading" }
  | { kind: "offline" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: KairosDailyOpportunities };

const marketLabels: Record<KairosOpportunityCandidate["market"], string> = {
  FIRST_HALF_MORE_GOALS: "Plus de buts en première période",
  SECOND_HALF_MORE_GOALS: "Plus de buts en seconde période",
  EQUAL_HALF_GOALS: "Autant de buts dans chaque période",
  FIRST_HALF_OVER_0_5: "1re période · au moins un but",
  SECOND_HALF_OVER_0_5: "2de période · au moins un but",
  SECOND_HALF_OVER_1_5: "2de période · au moins deux buts",
  HOME_OR_DRAW: "Double chance · domicile ou nul",
  AWAY_OR_DRAW: "Double chance · extérieur ou nul",
  HOME_OR_AWAY: "Double chance · sans nul"
};

export function KairosOpportunities() {
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
        const data = await createApiClient({
          timeoutMs: 10_000
        }).getDailyOpportunities();
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
                : "Le centre d’opportunités est temporairement indisponible."
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
      <section aria-busy="true" aria-label="Chargement des opportunités Kairos">
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
            ? "Aucune analyse ancienne n’est présentée comme actuelle."
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

  const data = state.data;
  const sections = [
    {
      title: "≥ 70 %",
      description: "Analyses qui franchissent tous les seuils centralisés.",
      items: data.opportunities.filter(
        (item) => item.safety_decision === "ANALYSIS_ALLOWED"
      )
    },
    {
      title: "Mi-temps",
      description: "Comparaison du volume de buts entre les deux périodes.",
      items: data.opportunities.filter((item) => item.section === "HALF_TIME")
    },
    {
      title: "Marchés de buts",
      description: "Signaux de buts par période, sans cote ni bookmaker.",
      items: data.opportunities.filter((item) => item.section === "GOAL_MARKETS")
    },
    {
      title: "Double chance",
      description: "Signal analytique B2.2 soumis au même gate B2.4.",
      items: data.opportunities.filter((item) => item.section === "DOUBLE_CHANCE")
    },
    {
      title: "À surveiller",
      description: "Le signal existe mais ne franchit pas toutes les barrières.",
      items: data.opportunities.filter((item) => item.section === "WATCH")
    },
    {
      title: "NO_BET",
      description: "Données insuffisantes ou garde-fou bloquant.",
      items: data.opportunities.filter((item) => item.section === "NO_BET")
    }
  ];

  return (
    <div className="opportunity-center">
      <section className="opportunity-summary" aria-label="Résumé des gates">
        <div>
          <span>Matchs évalués</span>
          <strong>{data.evaluated_match_count}</strong>
        </div>
        <div>
          <span>Seuil probabilité</span>
          <strong>{formatProbability(data.thresholds.estimated_probability)}</strong>
        </div>
        <div>
          <span>Échantillon résolu</span>
          <strong>{data.resolved_journal_sample_size}</strong>
        </div>
        <div>
          <span>Taux observé</span>
          <strong>
            {data.observed_hit_rate === null
              ? "Insuffisant"
              : formatProbability(data.observed_hit_rate)}
          </strong>
        </div>
      </section>

      {sections.map((section) => (
        <section className="opportunity-section" key={section.title}>
          <div className="opportunity-section-heading">
            <div>
              <span>Kairos · B2.4</span>
              <h2>{section.title}</h2>
            </div>
            <p>{section.description}</p>
          </div>
          {section.items.length ? (
            <div className="kairos-card-grid">
              {section.items.map((item) => (
                <OpportunityCard
                  item={item}
                  key={`${section.title}-${item.provider_match_id}`}
                />
              ))}
            </div>
          ) : (
            <p className="opportunity-empty">
              Aucun match ne satisfait cette section à cet instant.
            </p>
          )}
        </section>
      ))}

      <div className="kairos-safety-note">
        <Icon height={20} name="shield" width={20} />
        <div>
          {data.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      </div>
    </div>
  );
}

function OpportunityCard({ item }: { item: KairosMatchOpportunity }) {
  const primary = item.primary_analysis;
  return (
    <article className={`kairos-card ${primary === null ? "is-no-bet" : ""}`}>
      <div className="kairos-card-topline">
        <time dateTime={item.kickoff_at}>{formatDateTime(item.kickoff_at)}</time>
        <StatusBadge tone={primary === null ? "warning" : "cyan"}>
          {item.safety_decision}
        </StatusBadge>
      </div>
      <div className="kairos-fixture">
        <strong>{item.home_team_name}</strong>
        <span>contre</span>
        <strong>{item.away_team_name}</strong>
      </div>
      {primary ? (
        <>
          <div className="kairos-recommendation">
            <span>Analyse primaire</span>
            <h3>{marketLabels[primary.market]}</h3>
          </div>
          <div className="opportunity-probability">
            {formatProbability(primary.estimated_probability)}
          </div>
          <div className="kairos-badges">
            <StatusBadge tone="info">
              Qualité {primary.data_quality_score.toFixed(0)}
            </StatusBadge>
            <StatusBadge tone="neutral">
              Technique {primary.technical_confidence_score.toFixed(0)}
            </StatusBadge>
            <StatusBadge tone="warning">n={primary.sample_size}</StatusBadge>
          </div>
          <ul className="kairos-reason-list">
            {primary.reasons.slice(0, 3).map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
          {item.alternative_analyses.length > 0 && (
            <div className="opportunity-alternatives">
              <strong>Alternatives non corrélées retenues</strong>
              {item.alternative_analyses.map((alternative) => (
                <span key={alternative.market}>
                  {marketLabels[alternative.market]} ·{" "}
                  {formatProbability(alternative.estimated_probability)}
                </span>
              ))}
            </div>
          )}
        </>
      ) : (
        <p className="opportunity-no-bet">
          Aucune analyse ne franchit simultanément les seuils de probabilité,
          qualité, confiance technique et fraîcheur.
        </p>
      )}
    </article>
  );
}

function formatProbability(value: number): string {
  return new Intl.NumberFormat("fr-CD", {
    style: "percent",
    maximumFractionDigits: 1
  }).format(value);
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
