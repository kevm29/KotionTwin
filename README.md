# KotionTwin

Rejouer dans le navigateur les jeux web de **Motion Twin** (2004-2015), restaurés à partir de l'archive officielle
[motion-twin/WebGamesArchives](https://github.com/motion-twin/WebGamesArchives) (Hammerfest exclu).

- `index.html` : accueil et catalogue (recherche, filtres par collection et par état, tri, favoris, jeu au hasard).
- `collection.html?c=<collection>` : page d'une collection (KadoKado, Arkadeo, CaféJeux, Frutiparc, Muxxu, Motion Twin).
- `play.html?g=<id>` : page de jeu. Les SWF tournent dans [Ruffle](https://ruffle.rs) ; les portages HTML5 s'ouvrent dans une iframe.
  Écran de lancement, plein écran (touche F), coupure du son (M), manette tactile sur mobile, meilleurs scores locaux.
- `data/games.json` : le catalogue (146 jeux), source unique du site.
- `data/covers.json` + `assets/covers/` : vignettes des jeux sans capture d'origine (`tools/make_covers.py`).

Favoris, parties récentes, scores et thème clair/sombre sont enregistrés dans le navigateur du joueur (`localStorage`).
- `docs/INVENTAIRE.md` : inventaire technique de chaque jeu et méthode de restauration prévue.
- `docs/AJOUTER-UN-JEU.md` : comment restaurer un jeu et le rendre jouable.

## Lancer en local

```sh
python3 -m http.server 8000
# puis ouvrir http://localhost:8000/
```

Ruffle est chargé depuis jsDelivr (`@ruffle-rs/ruffle@0.7.1`). Pour travailler hors ligne, placez une copie de Ruffle
dans `vendor/ruffle/` (ignoré par git) : le site l'utilise en priorité.

## Régénérer l'inventaire

```sh
git clone --depth 1 https://github.com/motion-twin/WebGamesArchives ../WebGamesArchives
python3 -I tools/build_catalog.py ../WebGamesArchives
```

## Licence

Jeux et ressources © Motion Twin, licence CC BY-NC-SA 4.0. Projet de fan non commercial. Voir [CREDITS.md](CREDITS.md) et [LICENSE.md](LICENSE.md).
