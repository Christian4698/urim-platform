# API-Football Local Secret & Environment Preflight

La Phase 23 ajoute uniquement un preflight local pour verifier si l'environnement de l'operateur est pret pour un
futur smoke test API-Football manuel. Ce preflight ne lance aucun appel API-Football, n'active aucun fournisseur,
n'ajoute aucun endpoint public et n'ecrit rien en base.

## Regles invariantes
- Le preflight est local-only et terminal-only.
- Le preflight ne doit jamais etre lance depuis FastAPI.
- Aucun endpoint public ne doit exposer ce controle.
- Les valeurs sensibles restent uniquement dans l'environnement local de l'operateur.
- Aucune valeur sensible ne doit etre collee dans ChatGPT, Codex, Claude, Git, les docs, les logs ou `.env.example`.
- Aucune reference fournisseur brute ne doit etre affichee.
- Aucun payload brut provider ne doit etre stocke dans le repo.
- Aucune prediction, ingestion, cote, bookmaker, betting ou stake ne doit etre cree.

## Conditions verifiees
- L'environnement applicatif local n'est pas production.
- Le mode smoke local est explicitement active.
- Le mode read-only est confirme.
- L'absence de write DB est confirmee.
- L'absence de creation de prediction est confirmee.
- L'absence de betting est confirmee.
- Un materiel d'authentification local est present, sans affichage de sa valeur.
- Une reference provider locale est presente, sans affichage de sa valeur brute.
- Les routes publiques smoke/preflight plausibles sont absentes.
- Aucun materiel provider brut evident n'est detecte dans les artefacts locaux inspectes.
- `git status` clean est recommande avant le vrai smoke.

## Resultat public-safe
Le resultat partageable contient uniquement :

- `status` ;
- `ready_for_manual_smoke_attempt` ;
- `provider=api-football` ;
- `mode=local_secret_env_preflight_only` ;
- `secrets_detected_as_present=true/false` ;
- `provider_reference_present=true/false` ;
- confirmations booleennes de preflight ;
- `db_writes=false` ;
- `prediction_created=false` ;
- `betting_created=false` ;
- codes generiques de blocage.

Le resultat ne doit jamais contenir de valeur sensible, de reference fournisseur brute, de nom local sensible, de
payload provider brut, ni de sortie reseau.

## Refus ou not-ready
Le preflight doit retourner `not_ready_for_manual_smoke_attempt` si l'un de ces cas apparait :

- environnement production ;
- mode smoke local absent ;
- read-only non confirme ;
- no DB write non confirme ;
- no prediction non confirme ;
- no betting non confirme ;
- materiel d'authentification local absent ;
- reference provider locale absente ;
- route publique smoke/preflight detectee ;
- materiel provider brut detecte dans les artefacts locaux inspectes.

## Utilisation future
Depuis un terminal local dedie, l'operateur pourra executer le script local de preflight et lire uniquement le
resume public-safe. Toute sortie contenant une valeur sensible ou une reference brute doit etre consideree comme
non partageable et detruite.

Cette phase ne transforme pas le preflight en route, ne cree pas de commande provider reelle et ne remplace pas le
gate d'activation fournisseur.
