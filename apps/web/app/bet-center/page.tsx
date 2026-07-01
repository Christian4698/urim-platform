import { ModulePlaceholder } from "../../components/module-placeholder";

export default function BetCenterPage() {
  return (
    <ModulePlaceholder
      title="Bet Center"
      eyebrow="Virtual/internal"
      description="Internal-only skeleton for future risk views. No bookmaker is connected and no real betting can be executed."
      stateLabel="Virtual only"
      stateDetail="The Bet Center remains a locked UI shell with no financial execution path."
      emptyTitle="No real betting is available"
      emptyDescription="This page does not connect bookmakers, create stakes, recover losses, or execute any financial action."
      capabilities={[
        {
          label: "Bookmaker Access",
          status: "None",
          detail: "No bookmaker",
          tone: "danger"
        },
        {
          label: "Stake Execution",
          status: "Blocked",
          detail: "No stake execution",
          tone: "danger"
        },
        {
          label: "Betting Mode",
          status: "Virtual/internal",
          detail: "No real betting",
          tone: "warning"
        }
      ]}
    />
  );
}
