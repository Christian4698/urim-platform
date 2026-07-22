"use client";

import { useEffect, useState } from "react";
import { getSystemAvailability } from "../lib/api-client";
import {
  getSystemAvailabilityPresentation,
  type SystemAvailabilityState
} from "../lib/system-availability-state";
import { DataPanel, MetricRow, StatusBadge } from "./dashboard-ui";
import { Icon } from "./icon";

export function SystemAvailability({ detailed = false }: { detailed?: boolean }) {
  const [attempt, setAttempt] = useState(0);
  const [checkedAt, setCheckedAt] = useState<string | null>(null);
  const [state, setState] = useState<SystemAvailabilityState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;

    const loadAvailability = async () => {
      if (typeof navigator !== "undefined" && !navigator.onLine) {
        setState({ kind: "offline" });
        return;
      }

      setState({ kind: "loading" });
      try {
        const availability = await getSystemAvailability();
        if (!cancelled) {
          setState({ kind: "loaded", availability });
          setCheckedAt(
            new Intl.DateTimeFormat("fr-CD", {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit"
            }).format(new Date())
          );
        }
      } catch {
        if (!cancelled) {
          setState({
            kind: typeof navigator !== "undefined" && !navigator.onLine ? "offline" : "error"
          });
        }
      }
    };

    const handleOffline = () => setState({ kind: "offline" });
    const handleOnline = () => setAttempt((current) => current + 1);
    window.addEventListener("offline", handleOffline);
    window.addEventListener("online", handleOnline);
    void loadAvailability();

    return () => {
      cancelled = true;
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("online", handleOnline);
    };
  }, [attempt]);

  const presentation = getSystemAvailabilityPresentation(state);
  const statusTone =
    state.kind === "loaded"
      ? state.availability.service === "available"
        ? "success"
        : "warning"
      : state.kind === "loading"
        ? "info"
        : state.kind === "offline"
          ? "warning"
          : "danger";

  return (
    <DataPanel
      className={detailed ? "availability-panel availability-panel-detailed" : "availability-panel"}
      description="Contrôle direct des contrats publics FastAPI et de la sonde PostgreSQL."
      footer={
        <div className="availability-footer">
          <span>
            {state.kind === "loaded"
              ? `Backend ${state.availability.phase}${checkedAt ? ` · vérifié à ${checkedAt}` : ""}`
              : "Aucun détail de connexion, identifiant ou secret n’est exposé."}
          </span>
          <button
            className="refresh-button"
            disabled={state.kind === "loading"}
            onClick={() => setAttempt((current) => current + 1)}
            type="button"
          >
            <Icon height={16} name="refresh" width={16} />
            Actualiser
          </button>
        </div>
      }
      title="Disponibilité de la plateforme"
    >
      <div className="availability-summary">
        <StatusBadge tone={statusTone}>
          {state.kind === "loading"
            ? "Contrôle en cours"
            : presentation.service.value}
        </StatusBadge>
        <span>Frontend → FastAPI → PostgreSQL / Supabase</span>
      </div>
      <div
        aria-busy={state.kind === "loading"}
        aria-live="polite"
        className="metric-stack availability-status"
      >
        <MetricRow label="API FastAPI" {...presentation.api} />
        <MetricRow label="PostgreSQL / Supabase" {...presentation.database} />
        <MetricRow label="Chaîne applicative" {...presentation.service} />
      </div>
    </DataPanel>
  );
}
