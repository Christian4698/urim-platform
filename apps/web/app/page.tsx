import { appConfig } from "@urim/config";
import {
  DataPanel,
  MetricRow,
  PageHeader,
  StatCard,
  StatusBadge,
  SystemTable
} from "../components/dashboard-ui";

const readinessRows = [
  {
    label: "Provider Layer",
    status: "Disabled",
    detail: "No provider feed is connected in this frontend phase.",
    tone: "warning" as const
  },
  {
    label: "Kairos Signal",
    status: "Read-only",
    detail: "Signal surfaces are UI-only and produce no real prediction.",
    tone: "cyan" as const
  },
  {
    label: "Bet Center",
    status: "Virtual/internal",
    detail: "No bookmaker, no real betting, no stake execution.",
    tone: "danger" as const
  },
  {
    label: "Audit Mode",
    status: "Visible",
    detail: "Risk and limitation labels stay explicit in the interface.",
    tone: "info" as const
  }
];

const moduleRows = [
  {
    label: "Kairos Analysis",
    status: "Read-only skeleton",
    detail: "No real prediction",
    tone: "cyan" as const
  },
  {
    label: "Tickets",
    status: "Internal shell",
    detail: "No automated action",
    tone: "info" as const
  },
  {
    label: "Performance",
    status: "Evaluation shell",
    detail: "No production sports data",
    tone: "warning" as const
  },
  {
    label: "Post-Match Learning",
    status: "Learning shell",
    detail: "No real result ingestion",
    tone: "neutral" as const
  }
];

export default function DashboardPage() {
  return (
    <>
      <PageHeader
        eyebrow="URIM Command Surface"
        title="Dashboard URIM"
        description="A premium read-only skeleton for the Kairos engine, designed to show system posture without connecting sports data, providers, bookmakers, ML, or real betting."
      >
        <StatusBadge tone="cyan">Kairos Signal</StatusBadge>
        <StatusBadge tone="warning">Provider disabled</StatusBadge>
        <StatusBadge tone="danger">No real betting</StatusBadge>
      </PageHeader>

      <section className="stat-grid" aria-label="URIM system posture">
        <StatCard
          label="Kairos Signal"
          value="Read-only"
          status="No real prediction"
          tone="cyan"
          description="The intelligence surface is prepared for future phases without calculating live or pre-match outputs."
          meta={`Engine ${appConfig.engineName}`}
        />
        <StatCard
          label="Provider Layer"
          value="Disabled"
          status="No feed"
          tone="warning"
          description="No external connector, no provider payload, no production sports data."
          meta="Frontend shell only"
        />
        <StatCard
          label="Bet Center"
          value="Virtual only"
          status="Internal"
          tone="danger"
          description="Virtual/internal boundary with no bookmaker integration, no real stake, no financial execution."
          meta="Safety boundary"
        />
        <StatCard
          label="Audit Mode"
          value="Visible"
          status="Read-only"
          tone="info"
          description="Risk labels and product limitations remain explicit across the dashboard."
          meta={`${appConfig.defaultLocale} · ${appConfig.defaultCurrency}`}
        />
      </section>

      <section className="dashboard-layout" aria-label="URIM dashboard panels">
        <DataPanel
          title="System readiness"
          description="Static interface state for Phase Design 2. These rows are not live provider data."
          className="panel-wide"
        >
          <SystemTable caption="URIM system readiness" rows={readinessRows} />
        </DataPanel>

        <DataPanel
          title="Risk gates"
          description="Product guardrails remain visible before any future intelligence layer can be enabled."
        >
          <div className="metric-stack">
            <MetricRow
              label="Real prediction"
              value="Blocked"
              tone="danger"
              detail="Kairos does not publish predictions in this phase."
            />
            <MetricRow
              label="Provider feed"
              value="Disabled"
              tone="warning"
              detail="No external sports feed is connected."
            />
            <MetricRow
              label="Bet execution"
              value="None"
              tone="danger"
              detail="Bet Center remains virtual/internal only."
            />
            <MetricRow
              label="Frontend secrets"
              value="None"
              tone="success"
              detail="No provider credentials belong in the web app."
            />
          </div>
        </DataPanel>

        <DataPanel
          title="Module states"
          description="Navigation targets stay available while their future capabilities are clearly disabled."
          className="panel-wide"
        >
          <SystemTable caption="URIM module states" rows={moduleRows} />
        </DataPanel>
      </section>
    </>
  );
}
