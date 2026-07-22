import type { SystemAvailability } from "./api-client.ts";

type AvailabilityTone = "neutral" | "success" | "warning" | "danger" | "info";

export type SystemAvailabilityState =
  | { kind: "loading" }
  | { kind: "loaded"; availability: SystemAvailability }
  | { kind: "error" }
  | { kind: "offline" };

type AvailabilityMetric = {
  value: string;
  detail: string;
  tone: AvailabilityTone;
};

export type SystemAvailabilityPresentation = {
  api: AvailabilityMetric;
  database: AvailabilityMetric;
  service: AvailabilityMetric;
};

export function getSystemAvailabilityPresentation(
  state: SystemAvailabilityState
): SystemAvailabilityPresentation {
  if (state.kind === "loading") {
    const loadingMetric: AvailabilityMetric = {
      value: "Vérification",
      detail: "Connexion sécurisée au backend URIM en cours.",
      tone: "info"
    };
    return {
      api: loadingMetric,
      database: loadingMetric,
      service: loadingMetric
    };
  }

  if (state.kind === "offline") {
    return {
      api: {
        value: "Hors ligne",
        detail: "Aucune connexion réseau n’est disponible sur cet appareil.",
        tone: "warning"
      },
      database: {
        value: "Non vérifiée",
        detail: "PostgreSQL ne peut pas être interrogé hors ligne.",
        tone: "neutral"
      },
      service: {
        value: "Mode hors ligne",
        detail: "La navigation reste disponible; les données système ne sont pas mises en cache.",
        tone: "warning"
      }
    };
  }

  if (state.kind === "error") {
    return {
      api: {
        value: "Indisponible",
        detail: "Le backend URIM ne répond pas avec un contrat valide.",
        tone: "danger"
      },
      database: {
        value: "Inconnue",
        detail: "La base ne peut pas être vérifiée sans réponse backend valide.",
        tone: "warning"
      },
      service: {
        value: "Service indisponible",
        detail: "Réessayez après avoir vérifié la connexion et la configuration publique.",
        tone: "danger"
      }
    };
  }

  const databaseAvailable = state.availability.database === "available";
  return {
    api: {
      value: "En ligne",
      detail: "GET /health répond avec le contrat public attendu.",
      tone: "success"
    },
    database: {
      value: databaseAvailable ? "Disponible" : "Indisponible",
      detail: databaseAvailable
        ? "La sonde PostgreSQL de GET /readiness est opérationnelle."
        : "Le backend répond, mais sa connexion PostgreSQL est indisponible.",
      tone: databaseAvailable ? "success" : "warning"
    },
    service: {
      value: databaseAvailable ? "Opérationnel" : "Dégradé",
      detail: databaseAvailable
        ? "Frontend, API et base de données communiquent correctement."
        : "Les fonctionnalités dépendantes de la base restent bloquées.",
      tone: databaseAvailable ? "success" : "warning"
    }
  };
}
