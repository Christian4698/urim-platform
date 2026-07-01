import {
  DataPanel,
  EmptyState,
  MetricRow,
  PageHeader,
  StatusBadge,
  SystemTable,
  type Tone
} from "./dashboard-ui";

type ModuleCapability = {
  label: string;
  status: string;
  detail: string;
  tone?: Tone;
};

export function ModulePlaceholder({
  title,
  description,
  eyebrow,
  stateLabel,
  stateDetail,
  capabilities,
  emptyTitle,
  emptyDescription
}: {
  title: string;
  description: string;
  eyebrow: string;
  stateLabel: string;
  stateDetail: string;
  capabilities: ModuleCapability[];
  emptyTitle: string;
  emptyDescription: string;
}) {
  return (
    <>
      <PageHeader eyebrow={eyebrow} title={title} description={description}>
        <StatusBadge tone="cyan">Read-only skeleton</StatusBadge>
        <StatusBadge tone="warning">Provider disabled</StatusBadge>
      </PageHeader>

      <section className="dashboard-layout module-layout" aria-label={`${title} module shell`}>
        <DataPanel title="Module state" description={stateDetail}>
          <div className="metric-stack">
            <MetricRow
              label={title}
              value={stateLabel}
              tone="cyan"
              detail="Interface prepared for future phases only."
            />
            <MetricRow
              label="Production data"
              value="None"
              tone="danger"
              detail="No real sports data is displayed."
            />
            <MetricRow
              label="Provider access"
              value="Disabled"
              tone="warning"
              detail="No external provider call is made by this page."
            />
          </div>
        </DataPanel>

        <DataPanel
          title="Capability gates"
          description="These UI labels describe disabled capabilities, not live system output."
          className="panel-wide"
        >
          <SystemTable caption={`${title} capability gates`} rows={capabilities} />
        </DataPanel>
      </section>

      <EmptyState title={emptyTitle} description={emptyDescription}>
        <StatusBadge tone="danger">No real prediction</StatusBadge>
        <StatusBadge tone="warning">No provider feed</StatusBadge>
      </EmptyState>
    </>
  );
}
