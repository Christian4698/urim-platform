import { ModulePlaceholder } from "../../components/module-placeholder";

export default function SettingsPage() {
  return (
    <ModulePlaceholder
      title="Paramètres"
      eyebrow="Settings shell"
      description="Read-only settings skeleton for locale and product posture. No secrets or provider credentials are stored in the frontend."
      stateLabel="Read-only"
      stateDetail="Settings are visible as a UI shell only and do not write configuration or secrets."
      emptyTitle="No frontend secret storage"
      emptyDescription="Provider credentials, API keys, and backend security settings remain outside the web interface."
      capabilities={[
        {
          label: "Frontend Secrets",
          status: "None",
          detail: "No secrets in frontend",
          tone: "success"
        },
        {
          label: "Provider Credentials",
          status: "None",
          detail: "No provider credentials",
          tone: "danger"
        },
        {
          label: "Settings Write",
          status: "Disabled",
          detail: "No runtime configuration change",
          tone: "warning"
        }
      ]}
    />
  );
}
