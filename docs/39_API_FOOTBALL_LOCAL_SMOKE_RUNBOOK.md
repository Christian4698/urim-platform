# API-Football Local Smoke Runbook

La Phase 20 prepare uniquement la procedure securisee d'un futur smoke test API-Football local. Elle ne lance
aucun appel API-Football, n'ajoute aucune cle, n'ajoute aucune URL provider publique et n'active aucun provider
reel.

## Regles invariantes
- Le smoke test est local-only.
- Le smoke test ne doit jamais etre lance depuis une route FastAPI.
- Aucun endpoint public ne doit declencher le runner ou le smoke client.
- La cle API doit rester hors Git.
- La cle API ne doit jamais etre collee dans un prompt, ticket, message, log ou document.
- La cle API ne doit jamais etre ajoutee a `.env.example`.
- La cle API doit etre definie uniquement dans l'environnement local de l'operateur.
- L'environnement production doit refuser l'execution.
- Aucune donnee API-Football ne doit etre ecrite en DB.
- Aucune prediction ne doit etre creee depuis un smoke test.
- Aucun bookmaker, betting ou stake ne doit etre cree.
- Le resultat doit rester public-safe : statut, flags de securite et hash optionnel seulement.
- Aucun payload brut provider ne doit etre committe, stocke dans le repo ou partage publiquement.

## Checklist avant execution
- `git status` est clean.
- La branche courante est une branche dediee au smoke local.
- Le fichier d'environnement local existe hors Git et reste non tracke.
- La cle est absente du code source, des docs, des tests et des fichiers suivis.
- La cle est absente des logs existants.
- Docker et DB ne sont pas necessaires sauf validation locale explicite.
- `APP_ENV` ou son equivalent local indique un environnement non-production.
- Le mode smoke est explicitement active dans l'environnement local.
- Le mode read-only est explicitement confirme.
- Le mode non-production est explicitement confirme.
- L'absence de write DB est confirmee.
- L'absence de creation de prediction est confirmee.
- L'absence de betting, bookmaker et stake est confirmee.
- Le gate final d'activation provider reste bloque.
- Le transport est explicitement injecte par l'operateur local.
- La sortie attendue ne contient ni cle, ni credential, ni URL provider, ni payload brut.

## Procedure locale autorisee
1. Ouvrir un terminal local dedie.
2. Verifier la checklist avant execution.
3. Definir les valeurs sensibles uniquement dans ce terminal local, jamais dans un fichier suivi.
4. Executer le runner manuel local uniquement via le module Python interne.
5. Examiner uniquement le resume public-safe retourne.
6. Refuser, supprimer et ne pas partager toute sortie qui contient une valeur brute provider.

Cette procedure ne doit pas etre transformee en route FastAPI, job automatique, scheduler, queue, webhook ou
fallback production.

## Checklist apres execution
- Supprimer les variables sensibles du terminal.
- Fermer ou nettoyer l'historique du terminal si necessaire.
- Verifier `git status`.
- Verifier les logs locaux.
- Verifier l'absence de fichiers crees contenant secrets, credentials ou payloads bruts.
- Verifier l'absence de write DB.
- Verifier l'absence de vraie donnee provider dans le repo.
- Verifier l'absence de payload brut dans le repo.
- Verifier qu'aucune prediction, ingestion, bookmaker, betting ou stake n'a ete cree.
- Verifier qu'aucun endpoint public n'a ete ajoute.

## Criteres de refus
Refuser l'execution ou detruire la sortie locale si l'un de ces cas apparait :

- environnement production ;
- repo sale avant execution ;
- cle visible dans un fichier suivi, un log, un prompt ou une sortie console ;
- URL provider ou credential visible dans une sortie partageable ;
- payload brut provider ecrit dans le repo ;
- tentative d'appel depuis FastAPI ;
- tentative d'ecriture DB ;
- tentative de creation de prediction ;
- tentative de creation bookmaker, betting ou stake.

## Rapport attendu
Le rapport partageable doit contenir uniquement :

- date locale de l'execution ;
- branche ;
- statut safe ;
- `executed=true` ou `executed=false` ;
- confirmation read-only ;
- confirmation no DB write ;
- confirmation no prediction ;
- confirmation no betting ;
- hash optionnel du payload redacted ;
- risques restants.

Ne jamais inclure de cle, credential, URL provider, nom de variable locale sensible ou payload brut dans le
rapport.
