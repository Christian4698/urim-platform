# Sports Intelligence Bot — Codex Blueprint

Kit de conception et de gouvernance pour construire un bot d’analyse prédictive sportive fondé sur des données réelles, horodatées et traçables.

## Objectifs
- Produire des probabilités et des scénarios, jamais des certitudes.
- Séparer strictement pré-match, live et post-match.
- Refuser une prédiction lorsque les données sont insuffisantes, contradictoires ou trop anciennes.
- Conserver un snapshot immuable de chaque prédiction.
- Comparer les modèles au marché et aux baselines, pas seulement au taux de réussite.
- Connecter plusieurs fournisseurs via une couche canonique.
- Fournir une messagerie simple entre agents spécialisés.

## Démarrage avec Codex
1. Copier ce dossier à la racine du dépôt cible.
2. Lancer Codex depuis cette racine.
3. Demander : `Résume les instructions actives et les documents obligatoires avant toute implémentation.`
4. Utiliser `prompts/00_MASTER_CODEX_PROMPT.md`.
5. Exiger un plan dans `docs/exec-plans/active/` avant tout code.

## Principe central
> Aucune donnée de production ne doit être inventée, extrapolée comme si elle était observée, ou remplacée silencieusement par un mock.

Les données simulées sont autorisées uniquement dans les tests, fixtures locales et environnements explicitement marqués `DEMO`.
