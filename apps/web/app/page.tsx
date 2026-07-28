import type { Metadata } from "next";
import {
  ActionLink,
  DataPanel,
  FeatureCard,
  MetricRow,
  PageHeader,
  StatusBadge
} from "../components/dashboard-ui";

export const metadata: Metadata = {
  title: "Accueil",
  description:
    "Découvrez URIM, la plateforme d’intelligence sportive probabiliste, traçable et responsable.",
  alternates: { canonical: "/" }
};

export default function HomePage() {
  return (
    <>
      <section className="hero-section">
        <PageHeader
          description="URIM réunit une interface sobre, une API contrôlée, des données sportives auditables et Kairos Daily Suggestions en bêta analytique — sans live, bookmaker ni pari réel."
          eyebrow="Sports Intelligence Platform"
          title="Transformer l’incertitude en décisions explicables."
        >
          <ActionLink href="/dashboard">Ouvrir le dashboard</ActionLink>
          <ActionLink href="/modules" variant="secondary">
            Voir les modules
          </ActionLink>
        </PageHeader>

        <div className="hero-visual" aria-label="Principes URIM">
          <div className="hero-orbit hero-orbit-one" />
          <div className="hero-orbit hero-orbit-two" />
          <div className="hero-core">
            <span>KAIROS</span>
            <strong>Contrôle</strong>
            <small>Lecture seule</small>
          </div>
          <span className="hero-node hero-node-top">Traçable</span>
          <span className="hero-node hero-node-right">Prudent</span>
          <span className="hero-node hero-node-bottom">Explicable</span>
        </div>
      </section>

      <section className="trust-strip" aria-label="Garanties de la version publique">
        <div>
          <strong>B2.2</strong>
          <span>bêta analytique Kairos</span>
        </div>
        <div>
          <strong>0</strong>
          <span>secret côté navigateur</span>
        </div>
        <div>
          <strong>GET</strong>
          <span>API publique en lecture seule</span>
        </div>
        <div>
          <strong>NO_BET</strong>
          <span>plutôt qu’une fausse certitude</span>
        </div>
      </section>

      <section className="section-block" aria-labelledby="foundation-title">
        <div className="section-heading">
          <span className="eyebrow">Fondation produit</span>
          <h2 id="foundation-title">Une plateforme conçue pour mériter la confiance.</h2>
          <p>Chaque couche rend ses limites visibles avant d’ajouter de nouvelles capacités.</p>
        </div>
        <div className="feature-grid">
          <FeatureCard
            description="Le dashboard distingue clairement état réel, indisponibilité et fonctionnalités désactivées."
            icon="dashboard"
            title="Vue opérationnelle"
          >
            <StatusBadge tone="success">Disponible</StatusBadge>
          </FeatureCard>
          <FeatureCard
            description="Le navigateur interroge uniquement l’API URIM pour la santé, les données sportives et Kairos."
            icon="system"
            title="Disponibilité vérifiable"
          >
            <StatusBadge tone="cyan">Temps réel système</StatusBadge>
          </FeatureCard>
          <FeatureCard
            description="Les capacités sensibles restent bloquées tant que leurs conditions de sécurité ne sont pas remplies."
            icon="shield"
            title="Sécurité par défaut"
          >
            <StatusBadge tone="warning">Gates actifs</StatusBadge>
          </FeatureCard>
        </div>
      </section>

      <section className="dashboard-layout home-panels" aria-label="Périmètre actuel">
        <DataPanel
          description="Fonctions disponibles dans le Programme B2.2."
          title="Ce que vous pouvez utiliser"
        >
          <div className="metric-stack">
            <MetricRow
              detail="Navigation claire sur ordinateur, tablette et mobile."
              label="Interface"
              tone="success"
              value="Disponible"
            />
            <MetricRow
              detail="État public de l’API et de sa dépendance PostgreSQL."
              label="Disponibilité système"
              tone="success"
              value="Vérifiable"
            />
            <MetricRow
              detail="Inventaire transparent des fonctions actives et bloquées."
              label="Registre des modules"
              tone="success"
              value="Disponible"
            />
            <MetricRow
              detail="Suggestions analytiques en lecture seule avec garde-fou NO_BET."
              label="Kairos Daily Suggestions"
              tone="info"
              value="Bêta analytique"
            />
          </div>
        </DataPanel>

        <DataPanel
          description="Ces barrières ne sont pas contournables depuis l’interface."
          title="Limites volontaires"
        >
          <div className="metric-stack">
            <MetricRow
              label="Bookmakers & appels fournisseur frontend"
              tone="warning"
              value="Bloqués"
            />
            <MetricRow label="Live & exécution automatique" tone="warning" value="Désactivés" />
            <MetricRow label="Pari réel & authentification" tone="danger" value="Absents" />
          </div>
        </DataPanel>
      </section>
    </>
  );
}
