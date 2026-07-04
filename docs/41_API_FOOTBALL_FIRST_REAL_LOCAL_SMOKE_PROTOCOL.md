# API-Football First Real Local Smoke Protocol

La Phase 22 prepare uniquement le protocole final d'un futur premier smoke test API-Football reel et local. Elle
ne lance aucun appel API-Football, n'ajoute aucune cle, n'ajoute aucune reference fournisseur reelle et ne stocke
aucun payload provider.

## Regles invariantes
- La cle API ne doit jamais etre collee dans ChatGPT, Codex, Claude, Git, un ticket, une messagerie, une doc, un
  log ou `.env.example`.
- La cle API doit rester uniquement dans le terminal local de l'operateur ou dans un fichier local non tracke.
- Le test futur doit etre lance uniquement depuis le terminal local.
- Aucune route FastAPI, aucun endpoint public, aucun scheduler, aucune queue et aucun job automatique ne doit
  lancer le smoke.
- Aucune donnee provider ne doit etre ecrite en DB.
- Aucune ingestion canonique ne doit etre creee depuis ce smoke.
- Aucune prediction ne doit etre creee.
- Aucun bookmaker, betting, cote, stake ou placement reel ne doit etre cree.
- Le resultat affichable ou partageable doit rester public-safe.
- Tout payload brut provider doit rester hors repo.

## Checklist pre-smoke
- `git status` est clean.
- La branche courante est une branche dediee.
- `APP_ENV` ou son equivalent local indique un environnement non-production.
- Le mode smoke est explicitement active.
- Le mode read-only est confirme.
- L'absence de write DB est confirmee.
- L'absence de creation de prediction est confirmee.
- L'absence de betting, bookmaker et stake est confirmee.
- La cle est absente du code.
- La cle est absente des docs.
- La cle est absente de `.env.example`.
- Les logs sont prets a etre verifies.
- Aucun endpoint public n'est utilise.
- Le gate final d'activation provider reste bloque.
- La sortie attendue contient uniquement un resume public-safe.

## Commande future attendue
Cette section est un exemple de forme, pas une commande executable a copier telle quelle. Les valeurs locales
doivent etre definies uniquement dans le terminal local ou dans un fichier local non tracke.

```text
local-first-real-smoke \
  --auth-material SET_LOCAL_AUTH_MATERIAL_HERE \
  --provider-base-reference SET_LOCAL_PROVIDER_BASE_REFERENCE_HERE \
  --read-only confirmed \
  --non-production confirmed \
  --no-db-write confirmed \
  --no-prediction confirmed \
  --no-betting confirmed
```

Ne pas remplacer ces placeholders dans Git, dans une doc partagee ou dans un prompt. Ne pas ajouter de vraie
reference fournisseur, de vraie cle ou de payload brut autour de cette commande.

## Checklist post-smoke
- Supprimer les variables sensibles du terminal.
- Fermer ou nettoyer l'historique du terminal si necessaire.
- Verifier `git status`.
- Verifier l'absence de fichiers generes contenant des cles ou du materiel sensible.
- Verifier l'absence de payload brut dans le repo.
- Verifier l'absence de write DB.
- Verifier l'absence de prediction.
- Verifier l'absence de betting, bookmaker et stake.
- Verifier les logs sans cle ni reference brute fournisseur.
- Conserver uniquement un resume hashe et public-safe.

## Criteres de refus
Refuser l'execution future ou detruire la sortie locale si l'un de ces cas apparait :

- environnement production ;
- repo sale avant execution ;
- cle visible dans un fichier suivi, un log, un prompt ou une sortie partageable ;
- reference fournisseur brute visible dans une sortie partageable ;
- payload brut provider ecrit dans le repo ;
- tentative de lancement depuis FastAPI ;
- tentative d'ecriture DB ;
- tentative de creation de prediction ;
- tentative de creation bookmaker, betting, cote ou stake.

## Rapport public-safe attendu
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

Ne jamais inclure de cle, de reference fournisseur brute, de nom local sensible, de valeur locale sensible ou de
payload brut dans le rapport.
