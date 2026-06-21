# SECURITY.md

La politique détaillée se trouve dans `docs/17_SECURITY.md` et `docs/18_THREAT_MODEL.md`.

## Règles immédiates
- Clés API uniquement côté serveur, via un secret manager.
- `.env` jamais commité.
- Logs avec redaction.
- RBAC minimal : `viewer`, `analyst`, `operator`, `admin`.
- Actions administratives journalisées.
- Webhooks signés, horodatés et anti-rejeu.
- Aucun fournisseur B2B appelé directement depuis le navigateur.
- Respect des licences et restrictions de redistribution.
