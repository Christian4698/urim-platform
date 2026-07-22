export default function Loading() {
  return (
    <div aria-busy="true" aria-label="Chargement de la page" className="loading-state">
      <div className="skeleton skeleton-kicker" />
      <div className="skeleton skeleton-title" />
      <div className="skeleton skeleton-copy" />
      <div className="skeleton-grid">
        <div className="skeleton skeleton-card" />
        <div className="skeleton skeleton-card" />
        <div className="skeleton skeleton-card" />
      </div>
      <span className="sr-only">Chargement en cours…</span>
    </div>
  );
}
