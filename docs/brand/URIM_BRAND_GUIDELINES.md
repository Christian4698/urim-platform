# URIM Brand Guidelines

## Positionnement

URIM est une Sports Intelligence Platform premium. La marque exprime une
intelligence probabiliste, traçable, prudente et explicable. Elle ne promet
jamais un résultat garanti, un score exact, un pari sûr ou un bénéfice.

General Tech Consult est le propriétaire et créateur de la plateforme. Kairos
est le moteur d'intelligence interne d'URIM : il prépare, audite et explique les
signaux lorsque les phases produit autorisent des données réelles.

## Usage du logo

Le logo URIM est fourni en SVG vectoriel et en PNG transparent. Les SVG sont la
source privilégiée dans le frontend.

- Logo principal : `urim-logo-horizontal.svg`, à utiliser sur fonds sombres.
- Logo sur fond sombre : `urim-logo-on-dark.svg`, à utiliser quand un fond
  obsidian intégré est nécessaire.
- Logo sur fond clair : `urim-logo-on-light.svg`, à réserver aux surfaces
  Ice White.
- Logo vertical : `urim-logo-vertical.svg`, à utiliser pour des espaces
  verticaux ou supports institutionnels.
- Symbole : `urim-symbol.svg`, à utiliser pour favicon, app icon, marqueur de
  navigation compact ou état vide.
- Wordmark : `urim-wordmark.svg`, à utiliser lorsque le symbole est déjà
  présent dans la composition.

Clear space minimal : garder autour du logo un espace libre équivalent à la
largeur du fût central du symbole URIM. Aucun texte, bordure, badge ou icône ne
doit entrer dans cette zone.

Tailles minimales recommandées :

- Logo horizontal : 120 px de largeur en interface.
- Logo vertical : 72 px de largeur en interface.
- Symbole : 24 px de hauteur en interface, 32 px recommandé pour navigation.
- Favicon : utiliser les exports dédiés, ne pas redimensionner le logo complet.

Usages interdits :

- Ne pas recolorer les SVG en dehors des variantes validées.
- Ne pas ajouter de glow, texture, 3D, ombre agressive ou effet casino.
- Ne pas étirer, compresser, incliner ou rogner le logo.
- Ne pas placer le logo clair sur un fond clair sans variante adaptée.
- Ne pas intégrer le HTML de référence comme composant produit.
- Ne pas associer URIM à une promesse de gain, de certitude ou de pari forcé.

## Palette HEX

| Token | HEX | Rôle |
|---|---:|---|
| Deep Obsidian | `#05070B` | Fond principal dark |
| Midnight Navy | `#0B1220` | Cards, surfaces, élévation |
| Ice White | `#F4F7FB` | Texte principal et logo clair |
| Controlled Cyan | `#11D7FF` | Signal primaire, focus, action principale |
| Deep Blue Accent | `#2F6BFF` | Action secondaire, lien, sélection |
| Slate Gray | `#64748B` | Texte secondaire de référence |
| Success | `#22C55E` | Succès produit, validation |
| Warning | `#F59E0B` | Prudence, phase future, attention |
| Danger | `#EF4444` | Blocage, interdit, risque |
| Info | `#38BDF8` | Information neutre, état informatif |

Pour l'accessibilité sur fond sombre, le frontend peut utiliser des dérivés plus
clairs pour les paragraphes longs, tout en conservant les tokens de marque
ci-dessus comme source.

## Typographies

- Display / wordmark : Jost, fourni sous forme de tracés vectoriels dans le logo.
- Interface / body : Inter, avec fallback system sans-serif.
- Data / code / API : JetBrains Mono lorsque des identifiants, hashes ou champs
  techniques doivent être affichés.

Les interfaces doivent garder une typographie dense, lisible et professionnelle.
Pas de lettres serrées, pas de titre marketing surdimensionné dans les panneaux
opérationnels.

## Design Tokens Frontend

Les tokens CSS URIM vivent dans `apps/web/app/globals.css`.

- `--urim-deep-obsidian`
- `--urim-midnight-navy`
- `--urim-ice-white`
- `--urim-controlled-cyan`
- `--urim-deep-blue-accent`
- `--urim-slate-gray`
- `--success`
- `--warning`
- `--danger`
- `--info`

Les alias UI (`--background`, `--surface`, `--text`, `--text-muted`,
`--border`, `--accent`, `--focus-ring`) traduisent ces tokens en composants
réutilisables.

## Direction UI

L'interface URIM doit rester premium, sobre et opérationnelle :

- Fond principal dark Deep Obsidian.
- Surfaces de cards Midnight Navy avec bordures subtiles.
- Boutons et focus en Controlled Cyan, sans glow excessif.
- Badges arrondis, compacts et orientés statut.
- Visualisation de données propre, avec hiérarchie calme.
- Langage produit prudent : `NO_BET`, `INSUFFICIENT_DATA`, phase future et
  absence de données réelles doivent rester explicites quand c'est le cas.
- Aucun style casino, betting agressif, promesse de gain ou rendu IA décoratif.

## Inventaire des assets frontend

Assets copiés dans `apps/web/public/brand/logo/` :

- `urim-logo-horizontal.svg`
- `urim-logo-on-dark.svg`
- `urim-logo-on-light.svg`
- `urim-logo-vertical.svg`
- `urim-symbol.svg`
- `urim-wordmark.svg`

Assets copiés dans `apps/web/public/brand/icons/` :

- `urim-favicon.svg`
- `urim-favicon.png`
- `urim-app-icon-1024.png`

Source exports: external URIM brand package / assets provided by design tool. Les
planches palette ne sont pas intégrées comme assets UI.
