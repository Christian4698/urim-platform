import type { Metadata } from "next";
import {
  DataPanel,
  MetricRow,
  PageHeader,
  StatCard,
  StatusBadge,
  SystemTable
} from "../../components/dashboard-ui";
import { SystemAvailability } from "../../components/system-availability";

export const metadata: Metadata = {
  title: "Dashboard",
  description: "Vue opérationnelle et posture de sécurité de la plateforme URIM.",
  alternates: { canonical: "/dashboard" }
};

const moduleRows = [
  {
    label: "Dashboard",
    status: "Disponible",
    detail: "Vue opérationnelle de la version publique.",
    tone: "success" as const
  },
  {
    label: "Disponibilité système",
    status: "Disponible",
    detail: "Contrats GET /health et GET /readiness uniquement.",
    tone: "success" as const
  },
  {
    label: "Sources sportives",
    status: "Désactivées",
    detail: "Aucun fournisseur externe n’est appelé.",
    tone: "warning" as const
  },
  {
    label: "Intelligence prédictive",
    status: "Désactivée",
    detail: "Aucune probabilité ni prédiction officielle n’est produite.",
    tone: "warning" as const
  }
];

export default function DashboardPage() {
  return (
    <>
      <PageHeader
        description="Surveillez la chaîne publique URIM et vérifiez en un regard les capacités disponibles, dégradées ou volontairement bloquées."
        eyebrow="Vue opérationnelle"
        title="Dashboard"
      >
        <StatusBadge tone="cyan">Lecture système</StatusBadge>
        <StatusBadge tone="success">Contrats validés</StatusBadge>
        <StatusBadge tone="warning">Modules sensibles inactifs</StatusBadge>
      </PageHeader>

      <section className="stat-grid" aria-label="Indicateurs de périmètre">
        <StatCard
          description="Endpoints publics consommés par le navigateur."
          label="Surface API frontend"
          meta="GET /health · GET /readiness"
          status="Minimale"
          tone="cyan"
          value="2 routes"
        />
        <StatCard
          description="Aucune donnée confidentielle n’est embarquée dans le bundle."
          label="Secrets exposés"
          meta="DATABASE_URL reste côté serveur"
          status="Conforme"
          tone="success"
          value="Aucun"
        />
        <StatCard
          description="Fournisseurs, live, ML, bookmakers et paris réels."
          label="Capacités sensibles"
          meta="Blocage explicite"
          status="Sécurisé"
          tone="warning"
          value="Désactivées"
        />
        <StatCard
          description="La version publique ne crée aucune décision sportive."
          label="Décision produit"
          meta="Pas de conseil forcé"
          status="Prudent"
          tone="neutral"
          value="INSUFFICIENT_DATA"
        />
      </section>

      <section className="dashboard-layout" aria-label="État de la plateforme">
        <SystemAvailability />

        <DataPanel
          description="Contrôles immuables de cette version publique."
          title="Posture de sécurité"
        >
          <div className="metric-stack">
            <MetricRow
              detail="Origines exactes seulement, sans wildcard ni credentials."
              label="CORS"
              tone="success"
              value="Strict"
            />
            <MetricRow
              detail="Aucune variable de base de données côté navigateur."
              label="Secrets frontend"
              tone="success"
              value="Aucun"
            />
            <MetricRow
              detail="Aucun chemin financier dans le MVP."
              label="Pari réel"
              tone="danger"
              value="Bloqué"
            />
          </div>
        </DataPanel>

        <DataPanel
          className="panel-full"
          description="Inventaire explicite; aucun état n’est simulé comme une donnée réelle."
          title="État des modules"
        >
          <SystemTable caption="État des modules URIM" rows={moduleRows} />
        </DataPanel>
      </section>
    </>
  );
}
