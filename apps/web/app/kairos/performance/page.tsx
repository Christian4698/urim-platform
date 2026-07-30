import type { Metadata } from "next";
import { PageHeader, StatusBadge } from "../../../components/dashboard-ui";
import { KairosPerformanceDashboard } from "../../../components/kairos-performance";

export const metadata: Metadata = {
  title: "Performance Kairos",
  description:
    "Suivi descriptif et transparent des snapshots Kairos résolus, sans promesse de performance.",
  alternates: { canonical: "/kairos/performance" }
};

export default function KairosPerformancePage() {
  return (
    <>
      <PageHeader
        description="Résultats observés du journal append-only, segmentés sans confondre estimation, calibration et fréquence historique."
        eyebrow="Kairos · B2.4.1"
        title="Performance & calibration"
      >
        <StatusBadge tone="success">Lecture seule</StatusBadge>
        <StatusBadge tone="warning">30 résolutions minimum</StatusBadge>
        <StatusBadge tone="danger">Aucune promesse</StatusBadge>
      </PageHeader>
      <KairosPerformanceDashboard />
    </>
  );
}
