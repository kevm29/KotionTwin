# Restaurer un jeu et l'ajouter au site

Chaque jeu (ou groupe de jeux d'une même plateforme) est restauré sur sa propre branche puis fusionné dans `main` par pull request.

## Arborescence

```
games/<id>/            fichiers servis pour le jeu <id> (id = champ "id" de data/games.json)
  thumb.png|gif|jpg    vignette du catalogue (capture d'origine si elle existe)
  *.swf                SWF d'origine ou recompilés
  index.html           (portages HTML5 seulement)
platforms/<plateforme>/ code partagé : loader KadoKado, faux serveur Frusion, API Arkadeo, CaféJeux…
src/<id>/              sources modifiées ou recompilées (Haxe/AS/JS), avec un README qui explique comment rebâtir
```

Ne copiez dans `games/` que les fichiers dont le jeu a besoin à l'exécution (pas les `.fla`, ni l'archive entière : elle pèse 3,4 Go).

## Déclarer le jeu jouable

Dans `data/games.json`, pour l'entrée du jeu :

```json
"status": "jouable",             // "a-restaurer" | "en-cours" | "jouable"
"description": "Une ou deux phrases sur le principe du jeu.",
"controls": "Flèches pour bouger, Espace pour tirer.",
"entry": {
  "type": "ruffle",              // ou "html" pour un portage
  "swf": "games/<id>/loader.swf",
  "width": 300, "height": 320,   // taille d'origine de la scène
  "scale": 2,                    // agrandissement maximal
  "base": "games/<id>/",         // base des chargements relatifs du SWF
  "flashvars": { "swf": "game.swf" },
  "bgcolor": "#ffffff",
  "config": {}                   // options Ruffle supplémentaires si besoin
},
"notes": "Ce qui a été modifié, ce qui reste imparfait.",
"credits": "Motion Twin (jeu original) ; restauration KotionTwin"
```

`tools/build_catalog.py` peut être relancé : il conserve ces champs et n'ajoute que les jeux manquants.

## Liste de vérification avant de passer un jeu en « jouable »

1. **Images** : extraire toutes les images (`ffdec`/JPEXS sur les SWF, dossiers `bmp/`, `gfx/`, `img/`) et vérifier qu'aucune n'est vide, transparente à 100 % ou corrompue. Lister les manquantes.
2. **Sons et musiques** : la musique et les bruitages se lancent (après le clic de déblocage audio du navigateur).
3. **Animations** : les animations des sprites, transitions et écrans de titre jouent à la bonne vitesse (fps d'origine).
4. **Code** : la partie démarre, se joue jusqu'à la fin (game over / victoire) sans erreur dans la console ; le score s'affiche.
5. **Fidélité graphique** : comparer avec des captures d'époque (vignettes `sc*.gif`, `teaser.jpg`, captures web) : couleurs, polices, cadrage, taille de scène.
6. **Test automatique** : `node tools/smoke-swf.js <racine> '["/play.html?g=<id>"]' /tmp/shot 8000` puis regarder la capture.
7. **Crédits** : Motion Twin reste crédité ; toute ressource tierce est listée dans `CREDITS.md`.
