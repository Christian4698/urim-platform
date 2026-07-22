import type { Metadata } from "next";
import { appConfig } from "@urim/config";
import { DataPanel, MetricRow, PageHeader, StatusBadge } from "../../components/dashboard-ui";

export const metadata: Metadata = {
  title: "Paramètres",
  description: "Configuration publique et posture de confidentialité de la plateforme URIM.",
  alternates: { canonical: "/parametres" }
};

export default function SettingsPage() {
  return (
    <>
      <PageHeader
        description="Consultez la configuration publique de l’interface. Les secrets, paramètres serveur et credentials fournisseurs ne sont jamais modifiables depuis le navigateur."
        eyebrow="Configuration"
        title="Paramètres"
      >
        <StatusBadge tone="success">Configuration publique</StatusBadge>
        <StatusBadge tone="neutral">Sans authentification</StatusBadge>
      </PageHeader>

      <section className="dashboard-layout settings-layout" aria-label="Paramètres publics">
        <DataPanel description="Préférences de présentation définies par la plateforme." title="Interface">
          <div className="metric-stack">
            <MetricRow label="Langue" tone="cyan" value={appConfig.defaultLocale} />
            <MetricRow label="Devise de référence" tone="cyan" value={appConfig.defaultCurrency} />
            <MetricRow label="Thème" tone="neutral" value="Obsidian" />
            <MetricRow
              detail="Les animations respectent automatiquement le réglage système."
              label="Mouvement réduit"
              tone="success"
              value="Pris en charge"
            />
          </div>
        </DataPanel>

        <DataPanel description="Frontière entre configuration publique et serveur." title="Confidentialité">
          <div className="metric-stack">
            <MetricRow label="Clés API frontend" tone="success" value="Aucune" />
            <MetricRow label="DATABASE_URL" tone="success" value="Côté serveur" />
            <MetricRow label="Cookies de session" tone="success" value="Aucun" />
            <MetricRow label="Tracking publicitaire" tone="success" value="Aucun" />
          </div>
        </DataPanel>

        <DataPanel
          className="panel-full"
          description="Valeurs non sensibles utilisées par cette version."
          title="Environnement public"
        >
          <div className="settings-code-grid">
            <div>
              <span>Application</span>
              <strong>{appConfig.appName}</strong>
            </div>
            <div>
              <span>Moteur interne</span>
              <strong>{appConfig.engineName}</strong>
            </div>
            <div>
              <span>Version</span>
              <strong>{appConfig.appVersion}</strong>
            </div>
            <div>
              <span>Domaine officiel</span>
              <strong>urim.pro</strong>
            </div>
          </div>
        </DataPanel>
      </section>
    </>
  );
}
