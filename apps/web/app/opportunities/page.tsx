import type { Metadata } from "next";
import { PageHeader, StatusBadge } from "../../components/dashboard-ui";
import { KairosOpportunities } from "../../components/kairos-opportunities";

export const metadata: Metadata = {
  title: "Opportunity Center",
  description:
    "Centre d’analyses pré-match Kairos avec gates explicites, journal append-only et aucun pari.",
  alternates: { canonical: "/opportunities" }
};

export default function OpportunitiesPage() {
  return (
    <>
      <PageHeader
        description="Chaque match analysé expose une catégorie claire et uniquement des raisons de rejet sûres. Zéro opportunité est un résultat normal du gate, jamais une panne implicite."
        eyebrow="Kairos · B2.4.1"
        title="Half-Time & Opportunity Center"
      >
        <StatusBadge tone="cyan">Probabilité ≥ 70 %</StatusBadge>
        <StatusBadge tone="success">Lecture seule</StatusBadge>
        <StatusBadge tone="warning">Non calibré</StatusBadge>
        <StatusBadge tone="danger">Aucun pari</StatusBadge>
      </PageHeader>
      <KairosOpportunities />
    </>
  );
}
