# Plateforme KadoKado

`loader.swf` remplace le loader d'origine (`KadoKado/Games/api/loader.swf`), qui attendait le
serveur KadoKado (`gameinit.xml`, jetons, envoi des scores) et restait vide hors ligne.

## Utilisation dans `data/games.json`

```json
"entry": {
  "type": "ruffle",
  "swf": "platforms/kadokado/loader.swf",
  "base": "games/<id>/",
  "flashvars": { "swf": "game.swf", "gid": "<id>" },
  "width": 300, "height": 320, "scale": 2, "bgcolor": "#ffffff"
}
```

FlashVars :

| nom      | rôle |
|----------|------|
| `swf`    | SWF du jeu, relatif à `base` (défaut `game.swf`) |
| `gid`    | identifiant du jeu, clé du record local |
| `attach` | nom d'export du clip de code (défaut `90D*`, repli `code`) |
| `mt`     | `1` pour les anciens jeux MotionTypes : installe le runtime MT d'origine |

## Fonctionnement

1. Le loader définit l'API `KKApi` dans `_global`, sous son nom obfusqué **et** en clair.
   Les SWF KadoKado sont obfusqués par un hachage déterministe commun à tous les jeux :

   | clair | obfusqué | clair | obfusqué |
   |---|---|---|---|
   | KKApi | `;ndCG` | Manager | `980Sb` |
   | init | `}-B2` | main | `0D 6` |
   | available | `(kJ+1(` | isLocal | `03(H;` |
   | saveScore | `}(Rc5` | gameOver | `7T4cF(` |
   | setScore | `}B)Y_` | addScore | `5b)bA(` |
   | getScore | `{8}XA(` | const | `-Q)9)` |
   | aconst | `*G6KR` | cadd | `3B(*` |
   | cmult | `4u57)` | val | `8kN` |
   | flagCheater | `0ze*c` | registerButton | `7vdL6(` |
   | processing | `-p3G*` | getPeriod | `}Mzy-(` |
   | t | `]` | | |

   Les valeurs « protégées » `KKConst` sont de simples nombres.
2. Il charge le jeu dans un clip masqué à 300×300, attache le symbole de code exporté `90D*`
   (le scénario principal des jeux est vide), attend la fin de frame que `Manager` existe,
   appelle `Manager.init(clip)` puis `Manager.main()` à chaque frame (40 images/s, comme l'original).
3. Le bandeau du bas (300×20) affiche le score et le record. Le record est conservé dans un
   SharedObject (stockage local du navigateur via Ruffle). À la fin de partie, un écran
   « Partie terminée » propose de rejouer.
4. Le site peut écouter `window.KotionTwinKK(evenement, gid, score, record)` (`start`, `gameover`).

## Sons ajoutés (jeux d'origine muets)

Pour certains jeux, le loader enveloppe une méthode du jeu (noms obfusqués retrouvés avec
`tools/swfdis.py` et `tools/avm1dec.py`) et prévient la page par `ExternalInterface.call("ktSnd", type, valeur)`.
La page joue alors le son décrit dans `entry.sounds` de `data/games.json` (voir `assets/js/game-audio.js`),
avec deux curseurs de volume (bruitages, musique) sous le jeu.

| jeu | méthode enveloppée | son |
|---|---|---|
| Opalus 2 | `44{N.prototype["88rS("]` (une bulle éclate en débris) | `bulles`, 1 à 4 selon le nombre de bulles éclatées dans la même frame (1-3, 4-6, 7-11, 12+) |
| Opalus 2 | `638J.prototype[" 1qEn"]` (le cadre recalcule sa taille) | `gelee` quand le cadre grandit (aucun fichier pour l'instant) |
| Alchimie | `4FAK.prototype["5aiB)("]` (passage de l'état 0 à 1 de l'élément cible d'une fusion) | `element`, 1 à 12 selon le type fusionné |

## Reconstruire

Aucun compilateur Flash n'est nécessaire : `build/avm1c.py` est un petit compilateur
d'un sous-ensemble d'ActionScript 1 (syntaxe JavaScript) vers du bytecode AVM1.

```sh
sh platforms/kadokado/build/build.sh
```

`build/mt_runtime.bin` est le DoAction d'origine du runtime MotionTypes (sprite exporté `}ND*9`
du loader d'origine), réinjecté tel quel pour les anciens jeux.

## Tests

Ruffle 0.7.1 en local (`vendor/ruffle`). En navigateur headless, utiliser le moteur
`wgpu-webgl` : les moteurs `canvas` et `webgl` de Ruffle ne gèrent pas `BitmapData.draw`,
utilisé par plusieurs jeux (Alphabounce…).
