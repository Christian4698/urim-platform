import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { PageHeader, StatusBadge } from "../../components/dashboard-ui";
import { KairosSuggestions } from "../../components/kairos-suggestions";
import { isBusinessDate } from "../../lib/business-time";

export const metadata: Metadata = {
  title: "Suggestions Kairos",
  description:
    "Suggestions analytiques Kairos calculées en lecture seule depuis les données sportives locales.",
  alternates: { canonical: "/suggestions" }
};

export default async function SuggestionsPage({
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
        description="Une seule suggestion analytique par match, calculée depuis les observations déjà synchronisées. NO_BET reste la réponse normale lorsque les données ou le signal sont insuffisants."
        eyebrow="Kairos · B2.4.2"
        title="Suggestions Kairos"
      >
        <StatusBadge tone="cyan">Bêta analytique</StatusBadge>
        <StatusBadge tone="success">Lecture seule</StatusBadge>
        <StatusBadge tone="warning">Non calibré</StatusBadge>
        <StatusBadge tone="danger">Aucun pari</StatusBadge>
      </PageHeader>
      <KairosSuggestions initialDate={date} />
    </>
  );
}
