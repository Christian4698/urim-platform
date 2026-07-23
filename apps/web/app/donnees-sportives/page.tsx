import type { Metadata } from "next";
import { PageHeader, StatusBadge } from "../../components/dashboard-ui";
import { SportsDataOverview } from "../../components/sports-data-overview";

export const metadata: Metadata = {
  title: "Données sportives",
  description:
    "État read-only des compétitions, matchs et synchronisations API-Football d’URIM.",
  alternates: { canonical: "/donnees-sportives" }
};

export default function SportsDataPage() {
  return (
    <>
      <PageHeader
        description="Contrôle en lecture seule du pipeline API-Football vers FastAPI et PostgreSQL. Les informations absentes restent explicitement absentes."
        eyebrow="Programme B1"
        title="Données sportives"
      >
        <StatusBadge tone="success">Pipeline traçable</StatusBadge>
        <StatusBadge tone="warning">Kairos désactivé</StatusBadge>
      </PageHeader>
      <SportsDataOverview />
    </>
  );
}
