# Dinocard

Rebâtir : `python3 -I src/dinocard/build.py <WebGamesArchives>/Dinocard` (Pillow requis).

- `temple.swf` est le lecteur de combat d'origine, lancé tel quel. Il lit la flashvar `$info`
  (objet `mt.PersistCodec` : `$url`, `$imgUrl`, `$side`, `$endUrl`…), télécharge `$url` puis rejoue
  le combat reçu, lui aussi encodé avec PersistCodec.
- `games/dinocard/duel.js` remplace le serveur : il construit les decks et calcule un combat
  (pioche, énergies, œufs, éclosion, attaques, cimetière, points de vie) au format attendu par le
  lecteur (`$player1/2`, `$rounds[].$phases[].$turn1/2.$upkeep/$actions/$end`, `$combat`, `$elements`).
  Les types d'action utilisés : 0 dégâts, 1 état du dinoz, 2 vie, 3 réserve d'énergie, 4 cimetière,
  5 rail (pose d'un œuf), 8 pioche, 10 duel.
- Le décodeur PersistCodec du lecteur se trompe sur les renvois vers des noms de champs déjà vus :
  le combat est donc encodé avec `encode(fight, { refs: false })`.
- `index.html` intercepte les téléchargements du lecteur (`fetch`) pour servir le combat, les
  illustrations et `avatar.swf` en local ; la fin du combat arrive par `$endUrl = javascript:ktDinoEnd()`.
- La base des cartes n'étant pas dans l'archive, `cards.json` est générée depuis les illustrations
  (élément déduit de la teinte dominante, nom et caractéristiques tirés de façon déterministe).
