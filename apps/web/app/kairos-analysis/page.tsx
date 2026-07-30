import type { Metadata } from "next";
import {
  ActionLink,
  EmptyState,
  PageHeader,
  StatusBadge
} from "../../components/dashboard-ui";

export const metadata: Metadata = {
  title: "Analyses Kairos",
  description: "Accès aux analyses explicables des suggestions Kairos datées.",
  alternates: { canonical: "/kairos-analysis" }
};

export default function KairosAnalysisPage() {
  return (
    <>
      <PageHeader
        description="Les analyses détaillées s’ouvrent depuis une suggestion calculée sur les seules observations locales disponibles."
        eyebrow="Kairos · B2.2"
        title="Analyses Kairos"
      >
        <StatusBadge tone="success">Lecture seule</StatusBadge>
        <StatusBadge tone="danger">Aucun pari</StatusBadge>
      </PageHeader>
      <EmptyState
        description="Choisissez un match dans une liste datée. Kairos ne fabrique pas d’analyse pour un identifiant ou un match sans données suffisantes."
        title="Sélectionnez une suggestion"
      >
        <ActionLink href="/suggestions">Voir les suggestions Kairos</ActionLink>
      </EmptyState>
    </>
  );
}
