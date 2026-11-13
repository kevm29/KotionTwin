# Alphabounce

Rebâtir : `node src/alphabounce/build.mjs <WebGamesArchives>/Alphabounce`.

- `game.swf` est le client d'origine ; seul l'en-tête est corrigé (scène 400×360, valeur de `Cs.mcw/mch`).
- `data.json` reprend les constantes de `MissionInfo`/`ShopInfo`, les missions, les prix, les trous
  de ver et les planètes.
- `games/alphabounce/server.js` simule le serveur : il intercepte `fetch('/play/intercom?cmd=…')`,
  désérialise la requête Haxe (`platforms/flash8/haxeser.js`) et répond `<r>…</r>`. Les infos joueur
  sont encodées avec `mt.PersistCodec` (`platforms/flash8/persistcodec.js`, option `crc`).
- `?debug` dans l'URL affiche les requêtes dans la console.
