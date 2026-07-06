# API-Football First Real Local Smoke Execution

La Phase 24 ajoute uniquement un script local pour une future premiere tentative de smoke API-Football reel. Le
script reste terminal-only, local-only et public-safe. Les tests automatises utilisent uniquement un callable fake
et ne lancent aucun appel provider reel.

## Regles invariantes
- Le script doit etre lance uniquement depuis le terminal local.
- Le script ne doit jamais etre importe par FastAPI.
- Aucune route publique ne doit appeler le script.
- Les valeurs sensibles restent uniquement dans l'environnement local de l'operateur.
- Aucune valeur sensible ne doit etre affichee, loggee, documentee ou partagee.
- Aucune reference fournisseur brute ne doit etre affichee.
- Aucun payload brut provider ne doit etre affiche, stocke ou committe.
- Aucune donnee provider ne doit etre ecrite en DB.
- Aucune prediction, ingestion, cote, bookmaker, betting ou stake ne doit etre cree.

## Gates avant execution
- Le preflight local Phase 23 doit etre ready.
- L'environnement applicatif local n'est pas production.
- Le mode smoke local est explicitement active.
- Le materiel d'authentification local est present.
- La reference provider locale est presente.
- Le mode read-only est confirme.
- Le mode non-production est confirme.
- L'absence de write DB est confirmee.
- L'absence de creation de prediction est confirmee.
- L'absence de betting est confirmee.
- `git status` est clean.
- Le gate final provider Phase 15 reste bloque/safe.

## Runner PowerShell local
Un runner PowerShell local peut etre utilise pour eviter de ressaisir manuellement tous les drapeaux du premier
smoke reel :

```powershell
.\scripts\run_first_real_local_smoke.ps1
```

Le runner demande les valeurs operateur via prompts masques, refuse toute reference provider qui n'utilise pas un
schema chiffre, lance uniquement le script terminal local, puis restaure l'environnement du processus en fin
d'execution. Il ne doit jamais afficher la cle, afficher la reference provider brute, ecrire un fichier `.env`,
modifier `.env.example`, creer une route publique, ecrire en DB, creer une prediction, ou toucher a une logique
bookmaker, stake ou betting.

## Resultat public-safe
Le resultat partageable contient uniquement :

- `status` ;
- `executed` ;
- `provider=api-football` ;
- `mode=first_real_local_smoke_only` ;
- `payload_hash` si disponible ;
- `payload_top_level_keys` si disponible ;
- `db_writes=false` ;
- `prediction_created=false` ;
- `betting_created=false` ;
- codes generiques de blocage si la tentative est refusee.

Le resultat ne doit jamais contenir de cle, de reference fournisseur brute, de nom local sensible, de payload brut,
de donnee sportive brute ou de sortie reseau non redigee.

## Tests automatises
Les tests automatises doivent injecter un callable fake. Ils ne doivent jamais utiliser le chemin de requete locale
reelle, ne doivent ouvrir aucun socket provider et ne doivent ecrire aucune donnee.

Cette phase ne transforme pas le script en route, ne cree pas d'activation fournisseur et ne remplace pas le gate
d'activation provider.
