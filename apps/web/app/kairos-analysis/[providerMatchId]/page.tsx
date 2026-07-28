import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ActionLink, PageHeader, StatusBadge } from "../../../components/dashboard-ui";
import { KairosAnalysisDetail } from "../../../components/kairos-analysis-detail";

export const metadata: Metadata = {
  title: "Analyse Kairos",
  description: "Analyse détaillée, explicable et en lecture seule d’un match.",
  robots: { index: false, follow: false }
};

export default async function KairosMatchAnalysisPage({
  params,
  searchParams
}: {
  params: Promise<{ providerMatchId: string }>;
  searchParams: Promise<{ as_of?: string | string[] }>;
}) {
  const { providerMatchId } = await params;
  const { as_of: asOfParameter } = await searchParams;
  if (!/^[1-9][0-9]{0,15}$/.test(providerMatchId)) {
    notFound();
  }
  const matchId = Number(providerMatchId);
  if (!Number.isSafeInteger(matchId)) {
    notFound();
  }
  if (
    typeof asOfParameter !== "string" ||
    !/(?:Z|[+-][0-9]{2}:[0-9]{2})$/.test(asOfParameter) ||
    Number.isNaN(new Date(asOfParameter).getTime())
  ) {
    notFound();
  }

  return (
    <>
      <PageHeader
        description="Probabilités, facteurs favorables, facteurs défavorables et limites issus du même instant d’observation."
        eyebrow="Kairos · Analyse complète"
        title={`Match ${providerMatchId}`}
      >
        <ActionLink href="/suggestions" variant="secondary">
          Suggestions du jour
        </ActionLink>
        <StatusBadge tone="warning">Non calibré</StatusBadge>
      </PageHeader>
      <KairosAnalysisDetail asOf={asOfParameter} providerMatchId={matchId} />
    </>
  );
}
