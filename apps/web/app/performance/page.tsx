import { ModulePlaceholder } from "../../components/module-placeholder";

export default function PerformancePage() {
  return (
    <ModulePlaceholder
      title="Performance"
      eyebrow="Evaluation shell"
      description="Premium placeholder for future evaluation views. No production sports data, historical result, or ROI claim is displayed."
      stateLabel="Evaluation shell"
      stateDetail="Performance surfaces remain empty until real, governed, temporally valid data is available."
      emptyTitle="No performance claim is shown"
      emptyDescription="This page avoids win-rate, ROI, score, or certainty claims while the evaluation layer is inactive."
      capabilities={[
        {
          label: "Production Sports Data",
          status: "None",
          detail: "No production sports data",
          tone: "danger"
        },
        {
          label: "ROI Messaging",
          status: "Blocked",
          detail: "No ROI claim",
          tone: "danger"
        },
        {
          label: "Evaluation View",
          status: "Skeleton",
          detail: "No historical outcome table",
          tone: "warning"
        }
      ]}
    />
  );
}
