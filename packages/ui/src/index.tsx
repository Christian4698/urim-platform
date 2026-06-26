import type { ReactNode } from "react";

type Tone = "neutral" | "success" | "warning" | "danger" | "info";

const toneClasses: Record<Tone, string> = {
  neutral: "tone-neutral",
  success: "tone-success",
  warning: "tone-warning",
  danger: "tone-danger",
  info: "tone-info"
};

export function Card({
  title,
  description,
  children,
  footer,
  className = ""
}: {
  title?: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
}) {
  return (
    <section className={`ui-card ${className}`.trim()}>
      {(title || description) && (
        <header className="ui-card-header">
          {title && <h2>{title}</h2>}
          {description && <p>{description}</p>}
        </header>
      )}
      <div className="ui-card-body">{children}</div>
      {footer && <footer className="ui-card-footer">{footer}</footer>}
    </section>
  );
}

export function Badge({
  children,
  tone = "neutral"
}: {
  children: ReactNode;
  tone?: Tone;
}) {
  return <span className={`ui-badge ${toneClasses[tone]}`}>{children}</span>;
}

export function StatusPill({
  children,
  tone = "neutral"
}: {
  children: ReactNode;
  tone?: Tone;
}) {
  return <span className={`ui-status-pill ${toneClasses[tone]}`}>{children}</span>;
}

export function MetricCard({
  label,
  value,
  description,
  badge,
  tone = "neutral"
}: {
  label: string;
  value: string;
  description?: string;
  badge?: string;
  tone?: Tone;
}) {
  return (
    <article className="ui-metric-card">
      <div className="ui-metric-card-topline">
        <span>{label}</span>
        {badge && <Badge tone={tone}>{badge}</Badge>}
      </div>
      <strong>{value}</strong>
      {description && <p>{description}</p>}
    </article>
  );
}
