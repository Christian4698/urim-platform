# Plan d'exécution actif — Renommage produit vers URIM

Date : 2026-06-26
Phase : renommage documentaire isolé
Statut : actif

## Objectif
Renommer proprement le produit de `GTC Sports Prediction Agent` vers `URIM` sans changer la logique métier, sans connecter d'API réelle et sans affaiblir les garde-fous existants.

## Nomenclature officielle
- Application : `URIM`
- Nom court produit : `Urim`
- Cerveau analytique / moteur technique : `Kairos`
- Dashboard : `URIM Dashboard`
- Centre de mise : `Bet Center`
- Moteur de mise prudente : `Kairos Stake Guard`
- Propriétaire / créateur : `General Tech Consult` / `GTC`

## Règles de renommage
1. `GTC` ne doit plus désigner le produit.
2. `GTC` peut rester uniquement pour l'organisation propriétaire, créatrice ou comme signature technique.
3. `URIM` remplace les anciens noms lorsqu'ils désignent l'application.
4. `Kairos` remplace les formulations génériques du type moteur d'analyse ou technical brain lorsqu'elles désignent le cerveau analytique.
5. Les noms de modules doivent rester cohérents : `URIM`, `Kairos`, `Half Goals Intelligence Engine`, `Bet Center`, `Kairos Stake Guard`, `Post-Match Learning Engine`, `Corners Intelligence Engine`, `Fouls & Cards Intelligence Engine`, `NO_BET Engine`.
6. Aucun changement de logique métier, de sécurité, de temporalité ou de politique produit.

## Portée
- Documentation racine : `README.md`, `AGENTS.md`, `ARCHITECTURE.md`, `KIT_TREE.md`, `QUALITY_SCORE.md`
- Documentation sous `docs/`
- Prompts sous `prompts/`
- `SKILL.md` concernés sous `.agents/skills/`
- Exemples JSON et nomenclature textuelle associée

## Inventaire initial
- Occurrences détectées immédiatement :
  - `README.md` : `Sports Intelligence Bot`
  - `KIT_TREE.md` : `sports-intelligence-codex-blueprint`
- Vérifications complémentaires à mener :
  - mentions indirectes du produit dans les fichiers ciblés ;
  - mentions de `technical brain` et `moteur d'analyse` ;
  - cohérence des exemples JSON (`app_name`, `engine_name`, `currency`, `default_locale`) ;
  - cohérence entre produit, dashboard, moteur analytique et modules spécialisés.

## Étapes
1. Relire les fichiers explicitement demandés et les fichiers réellement touchés par l'inventaire.
2. Appliquer le renommage documentaire strictement dans le périmètre produit.
3. Mettre à jour les exemples JSON vers `URIM`, `Kairos`, `CDF`, `fr-CD`.
4. Contrôler les occurrences restantes des anciennes appellations.
5. Produire un récapitulatif : fichiers lus, modifiés, occurrences restantes, éléments conservés en `GTC`, risques et prochaine étape.

## Contraintes à préserver
- Aucune donnée fictive présentée comme réelle.
- Aucune fuite temporelle.
- Aucune promesse de réussite garantie.
- Aucun secret exposé.
- Aucun pari réel exécuté.
- Aucun garde-fou supprimé.
