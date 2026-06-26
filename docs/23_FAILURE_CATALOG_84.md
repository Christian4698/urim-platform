# Catalogue des 84 erreurs et failles — URIM / Kairos

## Erreur ultime

**La fuite temporelle** : utiliser directement ou indirectement une information qui n’était pas disponible au moment de la prédiction. Les erreurs E005, E029–E031 et E037–E039 sont bloquantes.

## Seconde confusion majeure

**Confondre taux de réussite et rentabilité.** Les erreurs E041–E062 couvrent les métriques, le prix et le risque financier.

| ID | Erreur | Description | Contrôle minimal |
|---|---|---|---|
| E001 | Données incomplètes | Absence de tirs, compositions, blessures, suspensions ou statistiques nécessaires. | Validation, provenance et multi-source |
| E002 | Données obsolètes | Analyse fondée sur une forme, un entraîneur ou un effectif périmé. | Validation, provenance et multi-source |
| E003 | Données incorrectes | Doublons, mauvais IDs, matchs reportés ou statuts erronés. | Validation, provenance et multi-source |
| E004 | Source unique non vérifiée | Une panne ou erreur fournisseur devient la vérité du système. | Validation, provenance et multi-source |
| E005 | Mauvaise synchronisation temporelle | Information reçue après coup considérée disponible avant la prédiction. | Temporal Guard + snapshot `as_of` + test bloquant |
| E006 | Composition probable prise pour officielle | Confusion entre estimation et annonce confirmée. | Validation, provenance et multi-source |
| E007 | Blessure mal contextualisée | Impact réel du joueur et qualité du remplaçant ignorés. | Validation, provenance et multi-source |
| E008 | Statistiques sans force d’opposition | Les performances contre adversaires faibles sont surévaluées. | Validation, provenance et multi-source |
| E009 | Compétitions mélangées | Championnat, coupe, amical et international traités pareillement. | Validation, provenance et multi-source |
| E010 | Flux live retardé | Le modèle agit sur une situation déjà dépassée. | Validation, provenance et multi-source |
| E011 | Couverture inégale | Le même niveau de confiance est affiché malgré des données très différentes. | Validation, provenance et multi-source |
| E012 | Contexte manquant | Météo, fatigue, enjeu, altitude ou rotation ignorés. | Validation, provenance et multi-source |
| E013 | Échantillon trop petit | Résultat instable présenté comme preuve générale. | Backtest chronologique + tests segmentés |
| E014 | Surapprentissage | Le modèle mémorise le passé et échoue hors échantillon. | Backtest chronologique + tests segmentés |
| E015 | Variables inutiles | Complexité et faux signaux augmentés sans gain reproductible. | Backtest chronologique + tests segmentés |
| E016 | Mauvaise gestion des nuls | Classe minoritaire mal apprise. | Backtest chronologique + tests segmentés |
| E017 | Déséquilibre des classes | Le modèle favorise mécaniquement le résultat dominant. | Backtest chronologique + tests segmentés |
| E018 | Un modèle pour toutes les ligues | Les différences structurelles entre compétitions sont ignorées. | Backtest chronologique + tests segmentés |
| E019 | Un modèle pour tous les marchés | 1X2, buts, corners et cartons sont confondus. | Backtest chronologique + tests segmentés |
| E020 | Indépendance fictive | Les événements corrélés sont mal modélisés. | Backtest chronologique + tests segmentés |
| E021 | Récence mal pondérée | Trop de poids aux vieux matchs ou aux derniers résultats. | Backtest chronologique + tests segmentés |
| E022 | Changement de régime ignoré | Nouvel entraîneur, mercato ou tactique non détectés. | Backtest chronologique + tests segmentés |
| E023 | Corrélation prise pour causalité | Une association statistique devient une fausse explication. | Backtest chronologique + tests segmentés |
| E024 | Confrontations directes surévaluées | Anciens matchs peu comparables dominent l’analyse. | Backtest chronologique + tests segmentés |
| E025 | Absence d’incertitude | Une réponse nette est produite malgré une forte ambiguïté. | Backtest chronologique + tests segmentés |
| E026 | Absence de NO_BET | Le système force un conseil sur chaque match. | Backtest chronologique + tests segmentés |
| E027 | Score exact surpromu | Un marché très dispersé est présenté comme hautement prévisible. | Backtest chronologique + tests segmentés |
| E028 | Explications post-hoc fabriquées | Le texte ne reflète pas réellement le calcul. | Backtest chronologique + tests segmentés |
| E029 | Split aléatoire temporel | Le futur peut entrer dans l’entraînement du passé. | Temporal Guard + snapshot `as_of` + test bloquant |
| E030 | Même dataset pour réglage et évaluation | Le test cesse d’être indépendant. | Temporal Guard + snapshot `as_of` + test bloquant |
| E031 | Prétraitement sur tout le dataset | Normalisation ou sélection voit le futur. | Temporal Guard + snapshot `as_of` + test bloquant |
| E032 | Meilleures périodes seulement | Les saisons perdantes sont cachées. | Backtest chronologique + tests segmentés |
| E033 | Meilleurs championnats choisis après test | Sélection opportuniste. | Backtest chronologique + tests segmentés |
| E034 | Trop de stratégies testées | Une réussite aléatoire est retenue comme signal. | Backtest chronologique + tests segmentés |
| E035 | Absence de vrai hors-échantillon | Le modèle n’est jamais confronté à des données vierges. | Backtest chronologique + tests segmentés |
| E036 | Pas de test live | Le backtest ignore latence, pannes et disponibilité réelle. | Backtest chronologique + tests segmentés |
| E037 | Cote de clôture utilisée trop tôt | Une information future du marché est injectée. | Temporal Guard + snapshot `as_of` + test bloquant |
| E038 | Lineup officielle utilisée trop tôt | Une composition non disponible à l’heure simulée est exploitée. | Temporal Guard + snapshot `as_of` + test bloquant |
| E039 | Statistiques de saison incluant le match cible | La réponse contamine les features. | Temporal Guard + snapshot `as_of` + test bloquant |
| E040 | Pas d’intervalle de confiance | 80 % sur un petit volume paraît équivalent à un grand volume. | Backtest chronologique + tests segmentés |
| E041 | Accuracy seule | La qualité probabiliste et le prix sont ignorés. | Calibration + baseline marché + métriques nettes |
| E042 | Calibration ignorée | Les probabilités annoncées ne correspondent pas aux fréquences. | Calibration + baseline marché + métriques nettes |
| E043 | Brier/log loss absents | La surconfiance n’est pas pénalisée. | Calibration + baseline marché + métriques nettes |
| E044 | Comparaison à une baseline faible | Le gain réel face au marché n’est pas prouvé. | Calibration + baseline marché + métriques nettes |
| E045 | Probabilités implicites ignorées | Le benchmark bookmaker manque. | Calibration + baseline marché + métriques nettes |
| E046 | Marge bookmaker ignorée | La probabilité de marché est mal calculée. | Calibration + baseline marché + métriques nettes |
| E047 | Bonne prédiction confondue avec pari rentable | Le prix et l’espérance sont oubliés. | Calibration + baseline marché + métriques nettes |
| E048 | Pas de métriques segmentées | Les faiblesses par ligue ou marché sont masquées. | Calibration + baseline marché + métriques nettes |
| E049 | Pré-match et live mélangés | Les résultats ne sont pas comparables. | Calibration + baseline marché + métriques nettes |
| E050 | Règles modifiées après résultats | Optimisation post-hoc. | Calibration + baseline marché + métriques nettes |
| E051 | Pertes supprimées | Historique falsifié. | Calibration + baseline marché + métriques nettes |
| E052 | Jours gagnants seulement | Cherry-picking. | Calibration + baseline marché + métriques nettes |
| E053 | 80 % confondu avec rentabilité | Une forte réussite peut perdre à faible cote. | Calibration + baseline marché + métriques nettes |
| E054 | Cote moyenne ignorée | Impossible d’évaluer la valeur réelle. | Calibration + baseline marché + métriques nettes |
| E055 | Martingale | Le risque explose après les pertes. | Calibration + baseline marché + métriques nettes |
| E056 | Mise excessive sur faible edge | Incertitude de modèle ignorée. | Calibration + baseline marché + métriques nettes |
| E057 | Exposition quotidienne illimitée | Risque agrégé non contrôlé. | Calibration + baseline marché + métriques nettes |
| E058 | Paris corrélés cumulés | Même scénario risque plusieurs positions. | Calibration + baseline marché + métriques nettes |
| E059 | Kelly avec probabilités non calibrées | La mise devient dangereusement surdimensionnée. | Calibration + baseline marché + métriques nettes |
| E060 | Contraintes réelles ignorées | Limites, slippage, suspensions ou annulations absents. | Calibration + baseline marché + métriques nettes |
| E061 | Coûts d’infrastructure ignorés | Rentabilité nette surévaluée. | Calibration + baseline marché + métriques nettes |
| E062 | Taux de réussite optimisé au lieu de la valeur | Objectif trompeur. | Calibration + baseline marché + métriques nettes |
| E063 | Modèle non réentraîné | Dégradation avec le temps. | Observabilité + immutabilité + sécurité |
| E064 | Drift non surveillé | Le changement de distribution passe inaperçu. | Observabilité + immutabilité + sécurité |
| E065 | Pas de secours fournisseur | Une panne arrête ou corrompt le produit. | Observabilité + immutabilité + sécurité |
| E066 | Fuseaux horaires mal gérés | Matchs et données sont décalés. | Observabilité + immutabilité + sécurité |
| E067 | Pas de journal immuable | Impossible de prouver ce qui avait été publié. | Observabilité + immutabilité + sécurité |
| E068 | Prédiction modifiée après le début | Historique réécrit. | Observabilité + immutabilité + sécurité |
| E069 | Pas de versionnement | Impossible de reproduire un résultat. | Observabilité + immutabilité + sécurité |
| E070 | Valeurs aberrantes ignorées | Erreurs extrêmes contaminent les calculs. | Observabilité + immutabilité + sécurité |
| E071 | Missing confondu avec zéro | Absence de donnée devient événement réel. | Observabilité + immutabilité + sécurité |
| E072 | Noms/IDs non testés | Mauvaises équipes ou saisons associées. | Observabilité + immutabilité + sécurité |
| E073 | Latence live non mesurée | Conseils périmés. | Observabilité + immutabilité + sécurité |
| E074 | Clés API mal protégées | Vol, coût et compromission. | Observabilité + immutabilité + sécurité |
| E075 | Promesse de pourcentage sans contexte | Marché, période et volume non précisés. | Politique produit + audit public |
| E076 | Probabilité présentée comme certitude | Risque trompeur. | Politique produit + audit public |
| E077 | Langage “match sûr” | Fausse garantie. | Politique produit + audit public |
| E078 | Périodes perdantes cachées | Performance commerciale biaisée. | Politique produit + audit public |
| E079 | Résultats modifiés rétroactivement | Fraude ou perte d’auditabilité. | Politique produit + audit public |
| E080 | Petites cotes choisies pour gonfler l’accuracy | Métrique cosmétique. | Politique produit + audit public |
| E081 | Pronostics contradictoires puis sélection du gagnant | Historique artificiel. | Politique produit + audit public |
| E082 | Série chanceuse prise pour compétence | Variance ignorée. | Politique produit + audit public |
| E083 | Incitation à récupérer les pertes | Comportement financier dangereux. | Politique produit + audit public |
| E084 | Limites non expliquées | Utilisateur privé du contexte de risque. | Politique produit + audit public |

## Règle CI
Toute pull request doit indiquer les IDs d’erreurs qu’elle prévient ou risque d’introduire.
