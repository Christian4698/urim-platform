"use client";

import { useEffect, useState } from "react";
import {
  ApiClientError,
  createApiClient,
  type KairosPerformance,
  type KairosPerformanceSegment
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
  | { kind: "error"; message: string }
  | { kind: "ready"; data: KairosPerformance };

export function KairosPerformanceDashboard() {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<ViewState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;
    createApiClient({ timeoutMs: 10_000 })
      .getKairosPerformance()
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
                : "Le rapport Kairos est temporairement indisponible."
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  if (state.kind === "loading") {
    return (
      <section aria-busy="true" className="skeleton-grid">
        {Array.from({ length: 4 }, (_, index) => (
          <span className="skeleton-card" key={index} />
        ))}
      </section>
    );
  }
  if (state.kind === "error") {
    return (
      <EmptyState description={state.message} title="Rapport indisponible">
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
  const sampleInsufficient = data.resolved_sample_size < 30;
  return (
    <div className="kairos-performance">
      <section className="stat-grid" aria-label="Résumé des performances Kairos">
        <StatCard
          description="Snapshots pré-match immuables, jamais réécrits."
          label="Snapshots"
          status="Journal"
          tone="cyan"
          value={String(data.total_snapshots)}
        />
        <StatCard
          description="SUCCESS et FAILURE uniquement."
          label="Résolutions valides"
          status={sampleInsufficient ? "Insuffisant" : "Descriptif"}
          tone={sampleInsufficient ? "warning" : "success"}
          value={String(data.resolved)}
        />
        <StatCard
          description="Résolutions exclues des taux observés."
          label="VOID"
          status="Exclu"
          value={String(data.void)}
        />
        <StatCard
          description="Snapshots encore sans résultat final admissible."
          label="Non résolus"
          status="En attente"
          value={String(data.unresolved)}
        />
      </section>

      <section className="performance-observed-rate">
        <div>
          <span>Taux observé</span>
          <strong>
            {sampleInsufficient
              ? "Échantillon insuffisant"
              : formatRate(data.observed_hit_rate)}
          </strong>
          <p>
            n={data.resolved_sample_size} résolutions valides. Une probabilité
            estimée n’est jamais présentée comme ce taux observé.
          </p>
        </div>
        <div>
          <span>Dernière résolution</span>
          <strong>{formatDateTime(data.last_resolution_at)}</strong>
          <p>Rapport généré {formatDateTime(data.last_report_generated_at)}.</p>
        </div>
      </section>

      <SegmentPanel
        description="Chaque marché reste visible, y compris sans échantillon."
        segments={data.performance_by_market}
        title="Performance par marché"
      />
      <SegmentPanel
        description="Segmentation descriptive par identifiant de compétition."
        segments={data.performance_by_competition}
        title="Performance par compétition"
      />
      <SegmentPanel
        description="La tranche provient de la probabilité estimée au snapshot."
        segments={data.performance_by_probability_band}
        title="Performance par tranche de probabilité"
      />
      <SegmentPanel
        description="La qualité décrit les données disponibles au moment de l’analyse."
        segments={data.performance_by_quality_level}
        title="Performance par niveau de qualité"
      />

      <DataPanel
        description="Comparaison descriptive entre estimation moyenne et fréquence observée. Aucun recalibrage n’est revendiqué."
        title="Buckets de calibration"
      >
        <PerformanceTable calibration segments={data.calibration_buckets} />
      </DataPanel>

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

function SegmentPanel({
  title,
  description,
  segments
}: {
  title: string;
  description: string;
  segments: KairosPerformanceSegment[];
}) {
  return (
    <DataPanel description={description} title={title}>
      {segments.length ? (
        <PerformanceTable segments={segments} />
      ) : (
        <p className="sports-panel-empty">
          Aucun snapshot n’est disponible pour cette segmentation.
        </p>
      )}
    </DataPanel>
  );
}

function PerformanceTable({
  segments,
  calibration = false
}: {
  segments: KairosPerformanceSegment[];
  calibration?: boolean;
}) {
  return (
    <div className="performance-table-wrap">
      <table className="performance-table">
        <thead>
          <tr>
            <th scope="col">Segment</th>
            <th scope="col">Snapshots</th>
            <th scope="col">Résolus</th>
            <th scope="col">VOID</th>
            <th scope="col">Non résolus</th>
            {calibration && <th scope="col">Estimation moyenne</th>}
            <th scope="col">Taux observé</th>
          </tr>
        </thead>
        <tbody>
          {segments.map((segment) => (
            <tr key={segment.key}>
              <th scope="row">{segment.label}</th>
              <td>{segment.total_snapshots}</td>
              <td>{segment.resolved_sample_size}</td>
              <td>{segment.void_count}</td>
              <td>{segment.unresolved_count}</td>
              {calibration && (
                <td>{formatRate(segment.estimated_probability_mean)}</td>
              )}
              <td>
                {segment.sample_status === "no_sample" ? (
                  <StatusBadge tone="neutral">Sans échantillon</StatusBadge>
                ) : segment.sample_status === "insufficient_sample" ? (
                  <StatusBadge tone="warning">
                    Échantillon insuffisant
                  </StatusBadge>
                ) : (
                  formatRate(segment.observed_hit_rate)
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatRate(value: number | null): string {
  if (value === null) return "Indisponible";
  return new Intl.NumberFormat("fr-CD", {
    style: "percent",
    maximumFractionDigits: 1
  }).format(value);
}

function formatDateTime(value: string | null): string {
  if (value === null) return "Aucune";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Indisponible";
  return new Intl.DateTimeFormat("fr-CD", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Africa/Kinshasa"
  }).format(parsed);
}
