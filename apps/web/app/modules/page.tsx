import type { Metadata } from "next";
import {
  DataPanel,
  PageHeader,
  StatusBadge,
  SystemTable
} from "../../components/dashboard-ui";

export const metadata: Metadata = {
  title: "Modules",
  description: "Registre transparent des modules disponibles et désactivés dans URIM.",
  alternates: { canonical: "/modules" }
};

const platformModules = [
  {
    label: "Dashboard",
    status: "Disponible",
    detail: "Synthèse du périmètre et de la posture de sécurité.",
    tone: "success" as const
  },
  {
    label: "Disponibilité système",
    status: "Disponible",
    detail: "Santé FastAPI et readiness PostgreSQL en lecture seule.",
    tone: "success" as const
  },
  {
    label: "Données sportives",
    status: "Disponible",
    detail: "Compétitions, matchs, synchronisations et fraîcheur en lecture seule.",
    tone: "success" as const
  },
  {
    label: "Kairos Daily Suggestions",
    status: "Bêta analytique",
    detail:
      "Suggestions quotidiennes calculées en lecture seule; NO_BET si les données sont insuffisantes ou périmées.",
    tone: "info" as const
  },
  {
    label: "Paramètres",
    status: "Disponible",
    detail: "Configuration publique et limites du produit.",
    tone: "success" as const
  }
];

const lockedModules = [
  {
    label: "API Football",
    status: "Contrôlée",
    detail: "Backend uniquement, désactivé sans clé ou flag explicite.",
    tone: "info" as const
  },
  {
    label: "Live",
    status: "Désactivé",
    detail: "Aucun flux temps réel sportif.",
    tone: "warning" as const
  },
  {
    label: "Bookmakers & paris réels",
    status: "Interdits",
    detail: "Aucun bookmaker, aucune cote, mise ou exécution financière.",
    tone: "danger" as const
  },
  {
    label: "Authentification",
    status: "Non activée",
    detail: "Aucun compte, session ou collecte d’identité dans la version actuelle.",
    tone: "neutral" as const
  }
];

export default function ModulesPage() {
  return (
    <>
      <PageHeader
        description="URIM affiche ce qui fonctionne aujourd’hui et ce qui reste volontairement verrouillé. Une fonction désactivée n’est jamais présentée comme disponible."
        eyebrow="Registre produit"
        title="Modules"
      >
        <StatusBadge tone="success">5 modules plateforme</StatusBadge>
        <StatusBadge tone="warning">4 capacités verrouillées</StatusBadge>
      </PageHeader>

      <section className="dashboard-layout modules-layout" aria-label="Registre des modules">
        <DataPanel
          description="Fonctions réellement utilisables dans cette version."
          title="Plateforme"
        >
          <SystemTable caption="Modules plateforme actifs" rows={platformModules} />
        </DataPanel>
        <DataPanel
          description="Gates de sécurité conservés pendant le Programme B2.2."
          title="Capacités sensibles"
        >
          <SystemTable caption="Modules sensibles désactivés" rows={lockedModules} />
        </DataPanel>
      </section>

      <DataPanel
        description="Kairos consomme les observations sportives déjà synchronisées sans les modifier. La suggestion analytique reste distincte du garde-fou et n’entraîne jamais une exécution de pari."
        title="Kairos Daily Suggestions · bêta analytique"
      >
        <div className="kairos-badges">
          <StatusBadge tone="neutral">Lecture seule</StatusBadge>
          <StatusBadge tone="warning">NO_BET garde-fou</StatusBadge>
          <StatusBadge tone="warning">Données insuffisantes ou périmées : blocage</StatusBadge>
          <StatusBadge tone="danger">Aucun pari réel</StatusBadge>
        </div>
      </DataPanel>
    </>
  );
}
