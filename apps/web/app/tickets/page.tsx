import { ModulePlaceholder } from "../../components/module-placeholder";

export default function TicketsPage() {
  return (
    <ModulePlaceholder
      title="Tickets"
      eyebrow="Internal ticket shell"
      description="Read-only workspace for future audit and workflow tickets. No automated action is created from this UI."
      stateLabel="Read-only"
      stateDetail="Ticket surfaces are visual placeholders only and cannot trigger provider, model, or betting actions."
      emptyTitle="Ticket workflow is inactive"
      emptyDescription="This shell can show future internal review states, but it does not create, route, or execute tickets."
      capabilities={[
        {
          label: "Ticket Creation",
          status: "Disabled",
          detail: "No automated action",
          tone: "warning"
        },
        {
          label: "Escalation",
          status: "Read-only",
          detail: "No workflow routing",
          tone: "cyan"
        },
        {
          label: "External Action",
          status: "None",
          detail: "No provider or bookmaker operation",
          tone: "danger"
        }
      ]}
    />
  );
}
