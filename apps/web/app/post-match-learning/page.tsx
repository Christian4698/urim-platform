import { ModulePlaceholder } from "../../components/module-placeholder";

export default function PostMatchLearningPage() {
  return (
    <ModulePlaceholder
      title="Post-Match Learning"
      eyebrow="Learning shell"
      description="Read-only placeholder for future learning loops. No real result ingestion or post-match payload is processed."
      stateLabel="Learning shell"
      stateDetail="Learning views stay inactive until temporal integrity and provenance requirements are implemented."
      emptyTitle="No result ingestion is active"
      emptyDescription="This UI does not ingest match results, update features, retrain models, or rewrite prior predictions."
      capabilities={[
        {
          label: "Result Ingestion",
          status: "Disabled",
          detail: "No real result ingestion",
          tone: "danger"
        },
        {
          label: "Temporal Guard",
          status: "Pending",
          detail: "Temporal guard pending",
          tone: "warning"
        },
        {
          label: "Model Update",
          status: "None",
          detail: "No ML or retraining",
          tone: "danger"
        }
      ]}
    />
  );
}
