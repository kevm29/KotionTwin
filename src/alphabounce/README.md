# Alphabounce

Rebâtir : `node src/alphabounce/build.mjs <WebGamesArchives>/Alphabounce` puis
`python3 -I src/alphabounce/gpu_colortransform.py games/alphabounce/game.swf`.

- `game.swf` est le client d'origine ; seul l'en-tête est corrigé (scène 400×360, valeur de `Cs.mcw/mch`).
- `data.json` reprend les constantes de `MissionInfo`/`ShopInfo`, les missions, les prix, les trous
  de ver et les planètes.
- `games/alphabounce/server.js` simule le serveur : il intercepte `fetch('/play/intercom?cmd=…')`,
  désérialise la requête Haxe (`platforms/flash8/haxeser.js`) et répond `<r>…</r>`. Les infos joueur
  sont encodées avec `mt.PersistCodec` (`platforms/flash8/persistcodec.js`, option `crc`).
- `?debug` dans l'URL affiche les requêtes dans la console.
- `gpu_colortransform.py` remplace `BitmapData.colorTransform` par un `ColorMatrixFilter` équivalent :
  les effets « plasma » restent ainsi entièrement sur la carte graphique dans Ruffle (sans quoi
  chaque image fait un aller-retour carte graphique ↔ processeur et le jeu rame).
- La page plafonne la résolution de rendu (1000 pixels de large, `?maxpx=` pour changer) puis
  agrandit : les flous et lueurs coûtent sinon proportionnellement à la taille de l'écran.
- Score : nombre de niveaux réussis (cases conquises). La page l'envoie au site avec
  `postMessage({type:'kotiontwin:progress'})` et le site l'enregistre quand on quitte la page.
