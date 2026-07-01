import type { ReactNode } from "react";

export type Tone = "neutral" | "success" | "warning" | "danger" | "info" | "cyan";

const toneClasses: Record<Tone, string> = {
  neutral: "tone-neutral",
  success: "tone-success",
  warning: "tone-warning",
  danger: "tone-danger",
  info: "tone-info",
  cyan: "tone-cyan"
};

export function StatusBadge({
  children,
  tone = "neutral"
}: {
  children: ReactNode;
  tone?: Tone;
}) {
  return <span className={`status-badge ${toneClasses[tone]}`}>{children}</span>;
}

export function PageHeader({
  eyebrow,
  title,
  description,
  children
}: {
  eyebrow: string;
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <header className="page-header premium-page-header">
      <StatusBadge tone="cyan">{eyebrow}</StatusBadge>
      <div className="page-header-copy">
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {children && <div className="page-header-actions">{children}</div>}
    </header>
  );
}

export function StatCard({
  label,
  value,
  status,
  description,
  tone = "neutral",
  meta
}: {
  label: string;
  value: string;
  status: string;
  description: string;
  tone?: Tone;
  meta?: string;
}) {
  return (
    <article className={`stat-card stat-card-${tone}`}>
      <div className="stat-card-topline">
        <span>{label}</span>
        <StatusBadge tone={tone}>{status}</StatusBadge>
      </div>
      <strong>{value}</strong>
      <p>{description}</p>
      {meta && <span className="stat-card-meta">{meta}</span>}
    </article>
  );
}

export function DataPanel({
  title,
  description,
  children,
  footer,
  className = ""
}: {
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
}) {
  return (
    <section className={`data-panel ${className}`.trim()}>
      <header className="data-panel-header">
        <div>
          <h2>{title}</h2>
          {description && <p>{description}</p>}
        </div>
      </header>
      <div className="data-panel-body">{children}</div>
      {footer && <footer className="data-panel-footer">{footer}</footer>}
    </section>
  );
}

export function MetricRow({
  label,
  value,
  detail,
  tone = "neutral"
}: {
  label: string;
  value: string;
  detail?: string;
  tone?: Tone;
}) {
  return (
    <div className="metric-row">
      <div>
        <span>{label}</span>
        {detail && <p>{detail}</p>}
      </div>
      <StatusBadge tone={tone}>{value}</StatusBadge>
    </div>
  );
}

export function SystemTable({
  caption,
  rows
}: {
  caption: string;
  rows: Array<{
    label: string;
    status: string;
    detail: string;
    tone?: Tone;
  }>;
}) {
  return (
    <div className="system-table-wrap">
      <table className="system-table">
        <caption>{caption}</caption>
        <thead>
          <tr>
            <th scope="col">Layer</th>
            <th scope="col">Status</th>
            <th scope="col">Scope</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label}>
              <th scope="row">{row.label}</th>
              <td>
                <StatusBadge tone={row.tone ?? "neutral"}>{row.status}</StatusBadge>
              </td>
              <td>{row.detail}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  children
}: {
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <section className="premium-empty-state">
      <div className="empty-state-mark" aria-hidden="true">
        UR
      </div>
      <div>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      {children && <div className="empty-state-actions">{children}</div>}
    </section>
  );
}
