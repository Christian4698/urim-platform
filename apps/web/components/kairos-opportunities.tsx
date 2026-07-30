"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  ApiClientError,
  createApiClient,
  type KairosDailyOpportunities,
  type KairosMatchOpportunity,
  type KairosOpportunityCandidate,
  type KairosRejectionReason
} from "../lib/api-client";
import {
  type BusinessDateSelection,
  formatBusinessDate,
  formatBusinessDateTime,
  resolveBusinessDateSelection
} from "../lib/business-time";
import { EmptyState, StatusBadge } from "./dashboard-ui";
import { Icon } from "./icon";
import { KairosDateNavigation } from "./kairos-date-navigation";

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

const rejectionLabels: Record<KairosRejectionReason, string> = {
  insufficient_half_time_data: "Historique mi-temps insuffisant",
  low_data_quality: "Qualité des données sous le seuil",
  low_technical_confidence: "Confiance technique sous le seuil",
  estimated_probability_below_threshold: "Estimation sous le seuil",
  stale_data: "Données périmées",
  critical_guardrail: "Garde-fou critique",
  correlated_market_excluded: "Marché corrélé exclu",
  provider_data_partial: "Données fournisseur partielles"
};

const missingDataLabels: Record<string, string> = {
  half_time_scores: "scores mi-temps",
  goal_events: "minutes des buts",
  h2h: "confrontations directes",
  standings: "classement",
  match_statistics: "statistiques de match"
};

export function KairosOpportunities({ initialDate }: { initialDate?: string }) {
  const [attempt, setAttempt] = useState(0);
  const [businessToday, setBusinessToday] = useState<string | null>(null);
  const [selection, setSelection] = useState<BusinessDateSelection>(
    initialDate === undefined
      ? { kind: "today" }
      : { kind: "date", date: initialDate }
  );
  const [state, setState] = useState<ViewState>({ kind: "loading" });
  const selectedDate =
    businessToday === null
      ? selection.kind === "date"
        ? selection.date
        : null
      : resolveBusinessDateSelection(selection, businessToday);
  const handleBusinessTodayChange = useCallback((date: string) => {
    setBusinessToday(date);
  }, []);
  const handleSelectionChange = useCallback(
    (nextSelection: BusinessDateSelection) => {
      setState({ kind: "loading" });
      setSelection(nextSelection);
    },
    []
  );

  useEffect(() => {
    if (selectedDate === null) {
      return;
    }
    let cancelled = false;
    const load = async () => {
      if (!navigator.onLine) {
        setState({ kind: "offline" });
        return;
      }
      setState({ kind: "loading" });
      try {
        const client = createApiClient({
          timeoutMs: 10_000
        });
        const data =
          selection.kind === "today"
            ? await client.getDailyOpportunities()
            : await client.getOpportunitiesForDate(selectedDate);
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
  }, [attempt, selectedDate, selection.kind]);

  const navigation = (
    <KairosDateNavigation
      businessToday={businessToday}
      consultedDate={
        state.kind === "ready" ? state.data.local_date : selectedDate
      }
      onBusinessTodayChange={handleBusinessTodayChange}
      onSelectionChange={handleSelectionChange}
      selection={selection}
    />
  );

  if (state.kind === "loading") {
    return (
      <div className="kairos-dated-view">
        {navigation}
        <section aria-busy="true" aria-label="Chargement des opportunités Kairos">
          <div className="kairos-card-grid">
            {Array.from({ length: 3 }, (_, index) => (
              <span className="skeleton-card kairos-card-skeleton" key={index} />
            ))}
          </div>
        </section>
      </div>
    );
  }

  if (state.kind === "offline" || state.kind === "error") {
    return (
      <div className="kairos-dated-view">
        {navigation}
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
      </div>
    );
  }

  const data = state.data;
  const sections = [
    {
      title: "Opportunités",
      description: "Tous les seuils analytiques et garde-fous sont franchis.",
      items: data.opportunities
    },
    {
      title: "À surveiller",
      description: "Le signal reste trop faible pour être publié comme opportunité.",
      items: data.evaluated_matches.filter((item) => item.section === "WATCH")
    },
    {
      title: "NO_BET",
      description: "Un garde-fou critique ou temporel bloque l’analyse.",
      items: data.evaluated_matches.filter((item) => item.section === "NO_BET")
    },
    {
      title: "Données insuffisantes",
      description: "Les valeurs absentes restent manquantes et ne sont jamais imputées.",
      items: data.evaluated_matches.filter(
        (item) => item.safety_decision === "INSUFFICIENT_DATA"
      )
    }
  ];

  return (
    <div className="kairos-dated-view">
      {navigation}
      <div className="opportunity-center">
      <section
        className={`opportunity-message is-${data.message_code}`}
        aria-live="polite"
      >
        <div>
          <span>
            Kairos · {formatBusinessDate(data.local_date) ?? data.local_date}
          </span>
          <strong>{data.message}</strong>
        </div>
        <Link className="action-link" href="/kairos/performance">
          Voir la performance historique
        </Link>
      </section>

      <section className="opportunity-summary" aria-label="Résumé des gates">
        <div>
          <span>Matchs évalués</span>
          <strong>{data.evaluated_match_count}</strong>
        </div>
        <div>
          <span>Opportunités</span>
          <strong>{data.opportunity_count}</strong>
        </div>
        <div>
          <span>À surveiller</span>
          <strong>{data.watchlist_count}</strong>
        </div>
        <div>
          <span>NO_BET</span>
          <strong>{data.no_bet_count}</strong>
        </div>
        <div>
          <span>Données insuffisantes</span>
          <strong>{data.insufficient_data_count}</strong>
        </div>
        <div>
          <span>Données périmées</span>
          <strong>{data.stale_data_count}</strong>
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
        <div>
          <span>Fraîcheur</span>
          <strong>{freshnessLabel(data.data_freshness.status)}</strong>
        </div>
      </section>

      <section className="opportunity-rejections">
        <div className="opportunity-section-heading">
          <div>
            <span>Explicabilité</span>
            <h2>Principales catégories de rejet</h2>
          </div>
          <p>
            Un même match peut cumuler plusieurs raisons sûres. Zéro
            opportunité n’est pas une panne.
          </p>
        </div>
        {Object.entries(data.rejection_reason_counts).length ? (
          <div className="opportunity-rejection-grid">
            {Object.entries(data.rejection_reason_counts)
              .sort((left, right) => right[1] - left[1])
              .map(([reason, count]) => (
                <div key={reason}>
                  <span>
                    {rejectionLabels[reason as KairosRejectionReason]}
                  </span>
                  <strong>{count}</strong>
                </div>
              ))}
          </div>
        ) : (
          <p className="opportunity-empty">
            Aucun rejet analytique n’est enregistré à cet instant.
          </p>
        )}
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
    </div>
  );
}

function OpportunityCard({ item }: { item: KairosMatchOpportunity }) {
  const primary = item.primary_analysis;
  return (
    <article className={`kairos-card ${primary === null ? "is-no-bet" : ""}`}>
      <div className="kairos-card-topline">
        <time dateTime={item.kickoff_at}>
          {formatBusinessDateTime(item.kickoff_at) ?? "Horaire indisponible"}
        </time>
        <StatusBadge tone={primary === null ? "warning" : "cyan"}>
          {item.safety_decision}
        </StatusBadge>
      </div>
      <div className="kairos-fixture">
        {item.competition_name !== null && (
          <span className="kairos-competition">{item.competition_name}</span>
        )}
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
        <>
          <p className="opportunity-no-bet">
            Aucune analyse ne franchit simultanément les seuils de probabilité,
            qualité, confiance technique et fraîcheur.
          </p>
          <ul className="kairos-reason-list">
            {item.rejection_reasons.map((reason) => (
              <li key={reason}>{rejectionLabels[reason]}</li>
            ))}
          </ul>
          {item.missing_data.length > 0 && (
            <p className="opportunity-missing">
              Données manquantes :{" "}
              {item.missing_data
                .map((field) => missingDataLabels[field])
                .join(", ")}
              .
            </p>
          )}
        </>
      )}
    </article>
  );
}

function freshnessLabel(
  status: KairosDailyOpportunities["data_freshness"]["status"]
): string {
  const labels = {
    fresh: "Fraîches",
    stale: "Périmées",
    partial: "Partielles",
    missing: "Absentes"
  };
  return labels[status];
}

function formatProbability(value: number): string {
  return new Intl.NumberFormat("fr-CD", {
    style: "percent",
    maximumFractionDigits: 1
  }).format(value);
}
