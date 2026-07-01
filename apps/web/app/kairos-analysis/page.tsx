import { ModulePlaceholder } from "../../components/module-placeholder";

export default function KairosAnalysisPage() {
  return (
    <ModulePlaceholder
      title="Kairos Analysis"
      eyebrow="Kairos Signal"
      description="Read-only skeleton for future probabilistic analysis surfaces. No real prediction is produced in this phase."
      stateLabel="Signal shell"
      stateDetail="Kairos remains internal and non-predictive while providers and model outputs are disabled."
      emptyTitle="Kairos Signal is not publishing"
      emptyDescription="This surface is ready for future explanatory workflows, but it does not calculate probabilities, advice, or match outcomes."
      capabilities={[
        {
          label: "Kairos Signal",
          status: "Read-only skeleton",
          detail: "No real prediction",
          tone: "cyan"
        },
        {
          label: "Provider Layer",
          status: "Disabled",
          detail: "No provider data available",
          tone: "warning"
        },
        {
          label: "Prediction Ledger",
          status: "Not writing",
          detail: "No immutable prediction is created",
          tone: "danger"
        }
      ]}
    />
  );
}
