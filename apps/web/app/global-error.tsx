"use client";

export default function GlobalError({ reset }: { reset: () => void }) {
  return (
    <html lang="fr-CD">
      <body>
        <main className="global-error-state">
          <span>URIM</span>
          <h1>Le service d’interface est momentanément indisponible.</h1>
          <p>Aucune donnée par défaut n’est présentée comme réelle.</p>
          <button onClick={reset} type="button">
            Réessayer
          </button>
        </main>
      </body>
    </html>
  );
}
