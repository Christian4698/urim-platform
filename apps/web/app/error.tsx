"use client";

import { useEffect } from "react";
import { Icon } from "../components/icon";

export default function ErrorPage({
  error,
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Keep the public UI neutral; runtime diagnostics remain in the hosting logs.
    void error.digest;
  }, [error]);

  return (
    <section className="route-state route-error" role="alert">
      <span className="eyebrow">Erreur contrôlée</span>
      <h1>Cette page n’a pas pu être affichée.</h1>
      <p>Aucune donnée de remplacement n’a été fabriquée. Vous pouvez relancer le rendu en sécurité.</p>
      <button className="state-action" onClick={reset} type="button">
        <Icon height={17} name="refresh" width={17} />
        Réessayer
      </button>
    </section>
  );
}
