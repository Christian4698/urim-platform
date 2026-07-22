import type { Metadata } from "next";
import { DataPanel, MetricRow, PageHeader, StatusBadge } from "../../components/dashboard-ui";
import { SystemAvailability } from "../../components/system-availability";

export const metadata: Metadata = {
  title: "Disponibilité système",
  description: "État public de la chaîne frontend, FastAPI et PostgreSQL d’URIM.",
  alternates: { canonical: "/disponibilite" }
};

export default function AvailabilityPage() {
  return (
    <>
      <PageHeader
        description="Cette page interroge en direct les deux endpoints publics autorisés. Elle affiche un état dégradé ou hors ligne au lieu d’inventer une valeur."
        eyebrow="Observabilité publique"
        title="Disponibilité système"
      >
        <StatusBadge tone="success">GET uniquement</StatusBadge>
        <StatusBadge tone="cyan">Actualisation manuelle</StatusBadge>
      </PageHeader>

      <SystemAvailability detailed />

      <section className="dashboard-layout availability-details" aria-label="Détails des contrôles">
        <DataPanel
          description="Ce que chaque réponse permet réellement de conclure."
          title="Contrats contrôlés"
        >
          <div className="metric-stack">
            <MetricRow
              detail="Confirme que FastAPI répond et respecte le schéma public."
              label="GET /health"
              tone="info"
              value="Santé API"
            />
            <MetricRow
              detail="Exécute une sonde PostgreSQL bornée côté backend."
              label="GET /readiness"
              tone="info"
              value="Dépendances"
            />
            <MetricRow
              detail="Les phases des deux réponses doivent être identiques."
              label="Cohérence"
              tone="success"
              value="Validée"
            />
          </div>
        </DataPanel>

        <DataPanel
          description="Données volontairement exclues de cette surface."
          title="Informations protégées"
        >
          <div className="metric-stack">
            <MetricRow label="DATABASE_URL" tone="success" value="Jamais exposée" />
            <MetricRow label="Erreurs de connexion" tone="success" value="Neutralisées" />
            <MetricRow label="Credentials fournisseurs" tone="success" value="Absents" />
          </div>
        </DataPanel>
      </section>
    </>
  );
}
