# Naturalchimie 2 (client Flash) pour KotionTwin

Le jeu de Motion Twin (2010), recompilé depuis `Naturalchimie2/fla/game/src` de WebGamesArchives
avec **Haxe 2.07** (cible Flash 8, AVM1), puis assemblé comme le faisait l'outil interne `swfmake`.

## Ce qui est fait

- `kotiontwin.patch` : ligne cassée dans `Game.hx` supprimée, artefacts absents de l'archive
  (`Slide`, `Skater`) retirés de `StageObject.hx`, vérification du domaine désactivée dans `Loader.hx`.
- `stubs/secure/Codec.hx` : **faux serveur**. `getData` fournit une « partie libre » (12 premiers
  éléments, dynamite, Alchimoth), `/act/start` répond avec le bon code de contrôle, `/act/end`
  envoie le score à la page (`ktSubmitScore`) puis appelle `ktGameEnded`.
- `stubs/mt/net/Codec.hx`, `stubs/mt/Timer.hx`, `stubs/mt/flash/Volatile.hx` : classes MT
  reconstituées (absentes de `libs-haxe2`).
- `objroot.as` + symbole `object` de KadoKado Alchimie 2 → `swf/objectMc.swf`. Le vrai
  `objectMc.swf` du site n'est que dans `fla/persos/library/objectMc.fla` (XFL CS5, non compilable ici).

## Limites

- Pas de carte, de quêtes, de PNJ, d'école ni de sauvegarde : seulement la partie au chaudron.
- Dessins des éléments : version KadoKado. Les rendus HD de `com/elements HD/` pourraient servir
  un jour pour les éléments 13 à 29.
- Le décor `img/bg/steampunk.jpg` et les MP3 chargés à la demande (`/sfx/*.mp3`, musique) ne sont
  pas dans l'archive : le décor est un dégradé fabriqué, et il n'y a pas de musique. Les 17 bruitages
  intégrés au SWF d'origine fonctionnent.

## Recompiler

Haxe 2.07 : paquet `haxe_2.07-1` d'Ubuntu (old-releases.ubuntu.com), extrait avec `dpkg -x`.

    WGA=/chemin/WebGamesArchives HAXE2=/chemin/h27 sh build.sh

Le dépôt WebGamesArchives doit contenir `Naturalchimie2`, `libs-haxe2` et `KadoKado/Games/alchimie2`.
