import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { PageHeader, StatusBadge } from "../../components/dashboard-ui";
import { KairosOpportunities } from "../../components/kairos-opportunities";
import { isBusinessDate } from "../../lib/business-time";

export const metadata: Metadata = {
  title: "Opportunity Center",
  description:
    "Centre d’analyses pré-match Kairos avec gates explicites, journal append-only et aucun pari.",
  alternates: { canonical: "/opportunities" }
};

export default async function OpportunitiesPage({
  searchParams
}: {
  searchParams: Promise<{ date?: string | string[] }>;
}) {
  const { date } = await searchParams;
  if (
    date !== undefined &&
    (typeof date !== "string" || !isBusinessDate(date))
  ) {
    notFound();
  }
  return (
    <>
      <PageHeader
        description="Chaque match analysé expose une catégorie claire et uniquement des raisons de rejet sûres. Zéro opportunité est un résultat normal du gate, jamais une panne implicite."
        eyebrow="Kairos · B2.4.2"
        title="Half-Time & Opportunity Center"
      >
        <StatusBadge tone="cyan">Probabilité ≥ 70 %</StatusBadge>
        <StatusBadge tone="success">Lecture seule</StatusBadge>
        <StatusBadge tone="warning">Non calibré</StatusBadge>
        <StatusBadge tone="danger">Aucun pari</StatusBadge>
      </PageHeader>
      <KairosOpportunities initialDate={date} />
    </>
  );
}
