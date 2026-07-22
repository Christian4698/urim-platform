import Link from "next/link";

export default function NotFound() {
  return (
    <section className="route-state">
      <span className="eyebrow">Erreur 404</span>
      <h1>Cette page n’existe pas.</h1>
      <p>Revenez à l’accueil ou consultez le registre des modules disponibles.</p>
      <div className="page-header-actions">
        <Link className="action-link action-link-primary" href="/">
          Retour à l’accueil
        </Link>
        <Link className="action-link action-link-secondary" href="/modules">
          Voir les modules
        </Link>
      </div>
    </section>
  );
}
