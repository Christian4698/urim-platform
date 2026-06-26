import { Badge, Card, StatusPill } from "@urim/ui";

export function ModulePlaceholder({
  title,
  description
}: {
  title: string;
  description: string;
}) {
  return (
    <>
      <header className="empty-state">
        <Badge tone="warning">PLACEHOLDER</Badge>
        <h1>{title}</h1>
        <p>{description}</p>
      </header>

      <Card
        title="Module en préparation — Phase future"
        description="Cet espace réserve l'interface sans afficher de donnée réelle ou de conseil de mise."
      >
        <StatusPill tone="danger">Aucune donnée de production fictive</StatusPill>
        <StatusPill tone="warning">Aucun appel API réel</StatusPill>
        <StatusPill tone="danger">Aucune recommandation forcée</StatusPill>
      </Card>
    </>
  );
}
