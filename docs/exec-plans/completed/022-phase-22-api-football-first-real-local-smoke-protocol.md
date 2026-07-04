# Phase 22 API-Football First Real Local Smoke Attempt Protocol

## Objectif
Preparer le protocole final qui permettra plus tard a un operateur de lancer un premier vrai smoke test local
API-Football, sans executer ce test pendant cette phase.

## Scope
- Ajouter une documentation operateur de protocole first-real local-only.
- Ajouter des tests documentation/safety pour bloquer les fuites de cle, de reference fournisseur et de payload brut.
- Mettre a jour la metadata de phase publique vers `phase-22-api-football-first-real-local-smoke-protocol`.
- Conserver le smoke client, le runner manuel et le harnais HTTP local-only des phases precedentes bloques par defaut.

## Hors scope
- Aucun appel API-Football reel.
- Aucune vraie cle API, reference fournisseur reelle ou URL provider.
- Aucun endpoint public, import FastAPI du harnais, scheduler, queue ou job automatique.
- Aucune ecriture DB, migration Alembic, modele DB, ingestion, prediction, ML, bookmaker, cote, stake ou betting.
- Aucun changement frontend, design, fixture d'ingestion, resultat provider reel ou payload brut committe.

## Regles de securite
- La cle ne doit jamais etre collee dans ChatGPT, Codex, Claude, Git, les docs, les logs ou `.env.example`.
- Le materiel sensible reste uniquement dans le terminal local de l'operateur ou dans un fichier local non tracke.
- Le test futur se lance uniquement depuis le terminal local, jamais depuis FastAPI.
- La sortie partageable reste public-safe : statut, confirmations de scope et hash optionnel seulement.
- Tout payload brut provider reste hors repo et doit etre detruit ou conserve uniquement selon une procedure locale non trackee.

## Validation
Depuis `apps/api` :

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

Depuis la racine :

```bash
git diff --check
```

`alembic check` reste conditionnel a un environnement DB/Docker local disponible.

## Risques couverts
- E005 : aucune donnee future ou provider reelle n'entre dans une prediction.
- E036 et E065 : le smoke reste un protocole local controle, sans activation provider.
- E074 : aucune cle API ou valeur sensible n'est exposee.
- E083 : aucune logique de betting, bookmaker ou stake n'est ajoutee.
- E084 : les limites du protocole et du rapport public-safe sont explicites.
