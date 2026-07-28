import type { Metadata } from "next";
import { PageHeader, StatusBadge } from "../../components/dashboard-ui";
import { KairosSuggestions } from "../../components/kairos-suggestions";

export const metadata: Metadata = {
  title: "Suggestions du jour",
  description:
    "Suggestions analytiques Kairos calculées en lecture seule depuis les données sportives locales.",
  alternates: { canonical: "/suggestions" }
};

export default function SuggestionsPage() {
  return (
    <>
      <PageHeader
        description="Une seule suggestion analytique par match, calculée depuis les observations déjà synchronisées. NO_BET reste la réponse normale lorsque les données ou le signal sont insuffisants."
        eyebrow="Kairos · B2.2"
        title="Suggestions du jour"
      >
        <StatusBadge tone="cyan">Bêta analytique</StatusBadge>
        <StatusBadge tone="success">Lecture seule</StatusBadge>
        <StatusBadge tone="warning">Non calibré</StatusBadge>
        <StatusBadge tone="danger">Aucun pari</StatusBadge>
      </PageHeader>
      <KairosSuggestions />
    </>
  );
}
