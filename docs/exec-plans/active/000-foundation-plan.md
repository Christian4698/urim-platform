# Phase 0 — Foundation Plan

Date : 2026-06-26
Statut : draft à valider avant implémentation
Produit : `URIM`
Cerveau analytique : `Kairos`
Organisation : `General Tech Consult` / `GTC`

## But de la phase
Préparer une base de travail propre, traçable et sécurisée pour construire `URIM` sans écrire de connecteur réel, sans modifier la logique métier existante et sans lancer d'implémentation tant que ce plan n'est pas validé.

## Contraintes non négociables
- Ne jamais utiliser une donnée future pour une prédiction passée.
- Ne jamais présenter une fixture, un mock ou une valeur par défaut comme une donnée réelle.
- Ne jamais exposer une clé API au frontend, dans les logs ou dans Git.
- Ne jamais promettre un taux de réussite, un bénéfice ou un score exact.
- Ne jamais forcer une décision si `NO_BET` ou `INSUFFICIENT_DATA` s'impose.
- Ne jamais modifier rétroactivement une prédiction publiée.
- Ne jamais connecter un fournisseur réel dans cette phase.
- Ne jamais implémenter directement sur `main` ; créer une branche dédiée après validation du plan.

## État constaté au départ
- Le dépôt est actuellement sur la branche `main`.
- Le worktree est déjà sale avant cette phase, avec des modifications documentaires et un répertoire `.claude/` non suivi.
- `ARCHITECTURE.md` duplique exactement `docs/03_SYSTEM_ARCHITECTURE.md`.
- `.claude/skills/` duplique les `SKILL.md` présents dans `.agents/skills/`.
- `.agents/skills/` est structurellement propre : un dossier par skill, un `SKILL.md` par dossier, aucun artefact additionnel.
- `docs/23_FAILURE_CATALOG_84.md` est exploitable pour un usage humain et de revue : 84 entrées structurées, contrôles minimaux, blocages temporels explicites et règle CI.

## Objectifs de sortie de la Phase 0
- Architecture cible confirmée.
- Périmètre MVP et modules prioritaires figés.
- Contrats de données et de connecteurs validés.
- Stratégie backend, frontend et base de données documentée.
- Exigences sécurité, temporalité, ledger et `NO_BET` transformées en gates de build/review.
- Plan de tests initial prêt avant toute implémentation.
- Liste de doublons à traiter ou à assumer explicitement.

## Périmètre détaillé

### 1. Architecture cible
- Confirmer le découpage `apps/web`, `apps/api`, `services/ingestion`, `services/prediction`, `services/live-engine`, `services/messaging`, `packages/contracts`, `packages/provider-sdk`, `infra`.
- Garder `Kairos` comme moteur analytique central.
- Garder `Kairos Stake Guard` et `NO_BET Engine` comme couche de décision bloquante.
- Prévoir `URIM Dashboard` et `Bet Center` comme consommateurs d'API, jamais comme détenteurs de secrets fournisseur.

### 2. Backend
- Définir l'API backend comme seul point d'entrée applicatif côté client.
- Geler les endpoints initiaux décrits dans `docs/21_API_AND_DATABASE_SPEC.md`.
- Prévoir validation stricte, RBAC, audit logs, redaction des logs et garde-fous SSRF.
- Préparer un service de publication append-only pour les prédictions et leurs versions.

### 3. Frontend
- Limiter la phase frontend à la structure, aux vues MVP et aux contrats d'interface.
- Interdire toute clé fournisseur et tout appel B2B direct depuis le navigateur.
- Prévoir l'affichage de provenance, fraîcheur, décisions `NO_BET`/`INSUFFICIENT_DATA`, version modèle et limites responsables.

### 4. Base de données
- Utiliser le modèle de tables de `docs/21_API_AND_DATABASE_SPEC.md` comme base.
- Conserver UTC, clés étrangères, contraintes d'unicité, index temporels et append-only.
- Réserver un stockage brut pour payloads référencés par `raw_hash` et `payload_location`.
- Prévoir la séparation entre observations fournisseur, modèle canonique, snapshots de features, prédictions, outcomes et audit logs.

### 5. Connecteurs API
- Phase 0 : aucun connecteur réel.
- Produire uniquement le cadre d'implémentation basé sur `docs/05_PROVIDER_CONNECTOR_CONTRACT.md`.
- Exiger `health()`, `capabilities()`, `coverage()`, `fetch_*`, `normalize(raw_payload)` et les métadonnées de provenance obligatoires.
- Prévoir timeouts, retries ciblés, backoff, jitter, circuit breaker, idempotence, quotas et cache distinct.

### 6. Sécurité
- Appliquer les exigences de `docs/17_SECURITY.md` et `docs/18_THREAT_MODEL.md`.
- Préparer secret scanning, politique `.env.example`, RBAC, redaction des logs, webhooks signés, anti-rejeu et contrôles supply chain.
- Interdire toute release avec secret exposé ou appel fournisseur frontend.

### 7. Tests
- Préparer la pyramide : unitaires, contrats, normalisation, intégration, temporalité, property-based, E2E, charge, sécurité et régression modèle.
- Rendre obligatoires les tests listés dans `docs/20_TESTING_STRATEGY.md`.
- Prévoir un mapping des tests vers les erreurs E001–E084 pour les futures PR.

### 8. Kairos Stake Guard / NO_BET Engine
- Geler les statuts `ADVICE`, `WATCH`, `NO_BET`, `INSUFFICIENT_DATA`, `SUSPENDED`.
- Définir cette couche comme autorité bloquante au-dessus de `Kairos`.
- Prévoir des règles initiales pour données anciennes, divergence, edge absent, cote stale, incident live, compétition hors domaine et calibration faible.

### 9. Temporal Guard
- Considérer E005, E029–E031 et E037–E039 comme bloquantes dès le départ.
- Imposer `available_at <= prediction_time` pour toute observation utilisée.
- Exiger des features calculées `AS OF prediction_time`, des splits chronologiques et un prétraitement fit uniquement sur train.
- Prévoir un test adversarial qui échoue si une ligne future peut être lue.

### 10. Ledger immuable
- Geler la stratégie append-only pour `predictions`, `prediction_versions`, `prediction_outcomes` et `audit_logs`.
- Exiger `immutable_hash`, versionnement, justification de correction et horodatage complet.
- Prévoir la traçabilité bout en bout : `provider request -> observation -> normalisation -> feature snapshot -> modèle -> risque -> publication`.

## Ordre proposé des travaux après validation
1. Créer une branche dédiée de fondation et ne pas travailler sur `main`.
2. Clarifier la politique de doublons documentaires et de miroirs de skills.
3. Figer les contrats canoniques et les schémas d'observation/prédiction.
4. Mettre en place l'ossature backend/frontend/packages/infra sans connecteur réel.
5. Ajouter migrations, tables append-only et primitives de ledger.
6. Ajouter les garde-fous sécurité et temporalité comme tests bloquants.
7. Ajouter les premiers tests de contrat, temporalité et immutabilité.
8. Valider la checklist Phase 0 avant d'ouvrir la phase suivante.

## Décisions reportées volontairement
- Choix final du framework backend si arbitrage encore ouvert.
- Choix final du stack frontend si arbitrage encore ouvert.
- Sélection du premier fournisseur réel.
- Implémentation du moteur live.
- Calibration finale et entraînement des modèles.

## Risques connus dès la phase 0
- Risque de divergence documentaire à cause du doublon exact `ARCHITECTURE.md` / `docs/03_SYSTEM_ARCHITECTURE.md`.
- Risque de divergence de skills à cause du miroir `.claude/skills/` vs `.agents/skills/`.
- Risque opérationnel car le dépôt est déjà sur `main` avec des changements non committés.
- Risque de confusion produit si d'anciens noms réapparaissent dans des futures contributions.
- Risque de fuite temporelle si les contrats `available_at` et `prediction_time` ne deviennent pas bloquants très tôt.

## Gates de validation avant implémentation
- Validation explicite de ce plan.
- Décision sur la politique de doublons documentaires et skills miroirs.
- Décision sur la branche de travail dédiée.
- Accord sur le périmètre MVP exact et les marchés initiaux.
- Accord sur les critères PASS/FAIL de Phase 0.

## Critères PASS/FAIL de la Phase 0
- PASS si le plan, l'architecture cible, les contrats, les invariants de sécurité, les invariants temporels, la stratégie de tests et la stratégie d'immutabilité sont validés.
- FAIL si un connecteur réel est ajouté, si un secret apparaît, si la temporalité n'est pas cadrée, si `NO_BET` n'est pas prévu comme garde-fou ou si le travail continue sur `main` sans décision explicite.

## Outils et extensions
- Pour cette phase documentaire, aucune extension supplémentaire n'est obligatoire.
- Les outils minimaux restent la lecture documentaire, la recherche de texte, le diff Git et les futurs tests locaux.

## Références directes
- `AGENTS.md`
- `QUALITY_SCORE.md`
- `docs/03_SYSTEM_ARCHITECTURE.md`
- `docs/05_PROVIDER_CONNECTOR_CONTRACT.md`
- `docs/06_DATA_PROVENANCE.md`
- `docs/07_TEMPORAL_INTEGRITY.md`
- `docs/13_NO_BET_AND_RISK_ENGINE.md`
- `docs/17_SECURITY.md`
- `docs/18_THREAT_MODEL.md`
- `docs/20_TESTING_STRATEGY.md`
- `docs/21_API_AND_DATABASE_SPEC.md`
- `docs/23_FAILURE_CATALOG_84.md`
