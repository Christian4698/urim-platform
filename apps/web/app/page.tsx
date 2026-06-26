import { appConfig, formatCurrency } from "@urim/config";
import { Badge, Card, MetricCard, StatusPill } from "@urim/ui";

export default function DashboardPage() {
  const placeholderCurrency = formatCurrency(1000);

  return (
    <>
      <header className="page-header">
        <Badge tone="warning">PLACEHOLDER — Phase 1</Badge>
        <h1>Dashboard URIM</h1>
        <p>
          Squelette applicatif pour préparer Kairos sans connecter de données sportives,
          bookmaker, modèle prédictif ou mise réelle.
        </p>
      </header>

      <section className="dashboard-grid" aria-label="État de la phase 1">
        <MetricCard
          label="Moteur"
          value="KAIROS_SLEEPING"
          badge="PLACEHOLDER"
          tone="warning"
          description="Aucune analyse réelle n'est calculée en Phase 1."
        />
        <MetricCard
          label="Données réelles"
          value="0 source"
          badge="VERROUILLÉ"
          tone="danger"
          description="Aucune API sportive réelle n'est connectée."
        />
        <MetricCard
          label="Devise par défaut"
          value={appConfig.defaultCurrency}
          badge="fr-CD"
          tone="info"
          description={`Exemple de formatage PLACEHOLDER : ${placeholderCurrency}.`}
        />
      </section>

      <section className="section-grid">
        <Card
          title="Modules préparés"
          description="Ces modules sont uniquement des points d'entrée visuels pour les phases futures."
        >
          <ul className="placeholder-list">
            <li>
              <span>Kairos Analysis</span>
              <StatusPill tone="warning">Module en préparation</StatusPill>
            </li>
            <li>
              <span>Bet Center</span>
              <StatusPill tone="danger">Aucune mise réelle</StatusPill>
            </li>
            <li>
              <span>Post-Match Learning</span>
              <StatusPill tone="info">Phase future</StatusPill>
            </li>
          </ul>
        </Card>

        <Card title="Garde-fous actifs" description="État produit Phase 1.">
          <StatusPill tone="danger">ENABLE_REAL_BETTING=false</StatusPill>
          <StatusPill tone="warning">ENABLE_LIVE=false</StatusPill>
          <StatusPill tone="danger">ALLOW_PRODUCTION_MOCKS=false</StatusPill>
        </Card>
      </section>
    </>
  );
}
