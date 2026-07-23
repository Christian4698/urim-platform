"use client";

import { useEffect, useState } from "react";
import {
  ApiClientError,
  createApiClient,
  type SportsDataSnapshot,
  type SportsMatch
} from "../lib/api-client";
import {
  DataPanel,
  EmptyState,
  StatCard,
  StatusBadge
} from "./dashboard-ui";
import { Icon } from "./icon";

type ViewState =
  | { kind: "loading" }
  | { kind: "offline" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: SportsDataSnapshot };

export function SportsDataOverview() {
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
        const data = await createApiClient({ timeoutMs: 10_000 }).getSportsData();
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
                : "Les données sportives sont temporairement indisponibles."
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
      <section aria-busy="true" aria-label="Chargement des données sportives">
        <div className="skeleton-grid sports-skeleton">
          {Array.from({ length: 4 }, (_, index) => (
            <span className="skeleton-card" key={index} />
          ))}
        </div>
      </section>
    );
  }

  if (state.kind === "offline") {
    return (
      <EmptyState
        description="La dernière observation ne peut pas être vérifiée sans connexion. URIM n’affiche aucune donnée mémorisée comme si elle était fraîche."
        title="Mode hors ligne"
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

  if (state.kind === "error") {
    return (
      <EmptyState description={state.message} title="Lecture impossible">
        <button
          className="refresh-button"
          onClick={() => setAttempt((current) => current + 1)}
          type="button"
        >
          <Icon height={17} name="refresh" width={17} />
          Actualiser
        </button>
      </EmptyState>
    );
  }

  const { data } = state;
  const providerTone =
    data.provider.status === "ready"
      ? "success"
      : data.provider.status === "degraded"
        ? "warning"
        : "neutral";
  const providerLabel =
    data.provider.status === "ready"
      ? "Prêt"
      : data.provider.status === "degraded"
        ? "À synchroniser"
        : "Désactivé";
  const latestSync = data.sync.latest;
  const freshResources = data.freshness.resources.filter(
    (resource) => resource.status === "fresh"
  ).length;

  return (
    <div className="sports-data-content" aria-live="polite">
      <section className="stat-grid" aria-label="Synthèse des données sportives">
        <StatCard
          description="Connexion backend uniquement, sans accès direct depuis le navigateur."
          label="API-Football"
          meta={`${data.provider.priority_competition_count} compétition(s) prioritaire(s)`}
          status={providerLabel}
          tone={providerTone}
          value={data.provider.connected ? "Connecté" : "En attente"}
        />
        <StatCard
          description="Compétitions normalisées et versionnées dans PostgreSQL."
          label="Compétitions"
          status={data.competitions.length ? "Observées" : "Vide"}
          tone={data.competitions.length ? "success" : "neutral"}
          value={String(data.competitions.length)}
        />
        <StatCard
          description="Matchs observés aujourd’hui dans le fuseau URIM."
          label="Matchs du jour"
          status={data.today.length ? "Disponibles" : "Aucun"}
          tone={data.today.length ? "info" : "neutral"}
          value={String(data.today.length)}
        />
        <StatCard
          description="Ressources situées dans leur fenêtre de fraîcheur."
          label="Fraîcheur"
          status={freshResources ? "Contrôlée" : "Manquante"}
          tone={freshResources ? "success" : "warning"}
          value={`${freshResources}/${data.freshness.resources.length}`}
        />
      </section>

      <section className="dashboard-layout sports-data-layout">
        <DataPanel
          description="Dernières versions observées. Les médias et payloads bruts ne sont pas publiés."
          title="Compétitions synchronisées"
        >
          {data.competitions.length ? (
            <div className="sports-competition-list">
              {data.competitions.map((competition) => (
                <article
                  className="sports-competition-row"
                  key={competition.provider_competition_id}
                >
                  <div>
                    <strong>{competition.name}</strong>
                    <span>
                      {competition.country_name ?? "Zone non renseignée"}
                      {competition.current_season
                        ? ` · Saison ${competition.current_season}`
                        : ""}
                    </span>
                  </div>
                  <StatusBadge
                    tone={
                      competition.freshness_status === "fresh" ? "success" : "warning"
                    }
                  >
                    {competition.freshness_status === "fresh" ? "Fraîche" : "À revoir"}
                  </StatusBadge>
                </article>
              ))}
            </div>
          ) : (
            <p className="sports-panel-empty">
              Aucune compétition réelle n’a encore été synchronisée.
            </p>
          )}
        </DataPanel>

        <DataPanel
          description="État public neutralisé du dernier job contrôlé."
          title="Dernière synchronisation"
        >
          {latestSync ? (
            <dl className="sports-sync-grid">
              <div>
                <dt>Commande</dt>
                <dd>{latestSync.sync_type}</dd>
              </div>
              <div>
                <dt>État</dt>
                <dd>{latestSync.status}</dd>
              </div>
              <div>
                <dt>Requêtes</dt>
                <dd>{latestSync.request_count}</dd>
              </div>
              <div>
                <dt>Ajouts / doublons</dt>
                <dd>
                  {latestSync.records_inserted} / {latestSync.records_duplicate}
                </dd>
              </div>
              <div>
                <dt>Fin</dt>
                <dd>{formatDateTime(latestSync.completed_at)}</dd>
              </div>
              <div>
                <dt>Quota restant</dt>
                <dd>{latestSync.quota_remaining_daily ?? "Non communiqué"}</dd>
              </div>
            </dl>
          ) : (
            <p className="sports-panel-empty">
              Aucun job de synchronisation n’a encore été enregistré.
            </p>
          )}
          {data.sync.recent_errors.length > 0 && (
            <div className="sports-public-error">
              <StatusBadge tone="warning">Erreur neutralisée</StatusBadge>
              <span>{data.sync.recent_errors[0]}</span>
            </div>
          )}
        </DataPanel>

        <DataPanel
          className="panel-full"
          description="Lecture sportive uniquement : aucune probabilité, sélection, cote ou recommandation."
          title="Matchs observés"
        >
          <MatchList
            emptyLabel="Aucun match observé aujourd’hui."
            matches={data.today}
            title="Aujourd’hui"
          />
          <MatchList
            emptyLabel="Aucun match à venir dans la fenêtre configurée."
            matches={data.upcoming}
            title="À venir · 7 jours"
          />
        </DataPanel>
      </section>

      <div className="sports-data-footer">
        <div>
          <StatusBadge tone="neutral">Lecture seule</StatusBadge>
          <StatusBadge tone="warning">Prédiction désactivée</StatusBadge>
          <StatusBadge tone="danger">Aucun pari réel</StatusBadge>
        </div>
        <button
          className="refresh-button"
          onClick={() => setAttempt((current) => current + 1)}
          type="button"
        >
          <Icon height={17} name="refresh" width={17} />
          Actualiser
        </button>
      </div>
    </div>
  );
}

function MatchList({
  title,
  matches,
  emptyLabel
}: {
  title: string;
  matches: SportsMatch[];
  emptyLabel: string;
}) {
  return (
    <section className="sports-match-section">
      <h3>{title}</h3>
      {matches.length ? (
        <div className="sports-match-list">
          {matches.map((match) => (
            <article className="sports-match-row" key={match.provider_match_id}>
              <time dateTime={match.kickoff_at}>{formatDateTime(match.kickoff_at)}</time>
              <div>
                <strong>{match.home_team_name}</strong>
                <span>contre</span>
                <strong>{match.away_team_name}</strong>
              </div>
              <StatusBadge
                tone={match.freshness_status === "fresh" ? "info" : "warning"}
              >
                {match.status_short}
              </StatusBadge>
            </article>
          ))}
        </div>
      ) : (
        <p className="sports-panel-empty">{emptyLabel}</p>
      )}
    </section>
  );
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return "Non disponible";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Non disponible";
  }
  return new Intl.DateTimeFormat("fr-CD", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Africa/Kinshasa"
  }).format(parsed);
}
