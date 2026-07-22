import Link from "next/link";
import type { ReactNode } from "react";
import { Icon, type IconName } from "./icon";

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
    <header className="page-header">
      <span className="eyebrow">{eyebrow}</span>
      <div className="page-header-copy">
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {children && <div className="page-header-actions">{children}</div>}
    </header>
  );
}

export function ActionLink({
  href,
  children,
  variant = "primary"
}: {
  href: string;
  children: ReactNode;
  variant?: "primary" | "secondary";
}) {
  return (
    <Link className={`action-link action-link-${variant}`} href={href}>
      <span>{children}</span>
      <Icon height={17} name="arrow" width={17} />
    </Link>
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

export function FeatureCard({
  icon,
  title,
  description,
  children
}: {
  icon: IconName;
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <article className="feature-card">
      <div className="feature-icon">
        <Icon height={22} name={icon} width={22} />
      </div>
      <div>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      {children && <div className="feature-card-footer">{children}</div>}
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
            <th scope="col">Composant</th>
            <th scope="col">État</th>
            <th scope="col">Périmètre</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label}>
              <th data-label="Composant" scope="row">
                {row.label}
              </th>
              <td data-label="État">
                <StatusBadge tone={row.tone ?? "neutral"}>{row.status}</StatusBadge>
              </td>
              <td data-label="Périmètre">{row.detail}</td>
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
    <section className="empty-state-panel">
      <div className="empty-state-mark" aria-hidden="true">
        <ImageMark />
      </div>
      <div>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      {children && <div className="empty-state-actions">{children}</div>}
    </section>
  );
}

function ImageMark() {
  return <span>UR</span>;
}
