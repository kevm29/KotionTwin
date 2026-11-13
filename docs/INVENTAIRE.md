# Inventaire technique de WebGamesArchives

Inventaire de l'archive [motion-twin/WebGamesArchives](https://github.com/motion-twin/WebGamesArchives) (licence CC BY-NC-SA 4.0), Hammerfest exclu. Généré par `tools/build_catalog.py`, complété à la main. Les chiffres comptent les fichiers présents dans le dossier source du jeu.

## Synthèse

- **146 jeux** recensés dans 6 collections. `TwinoidGoals` (icônes de succès Twinoid), `libs-haxe2` et `libs-haxe3` (bibliothèques partagées) ne sont pas des jeux.
- Trois méthodes de restauration :
  - **Ruffle + API simulée** : le SWF compilé d'origine existe. Il tourne dans [Ruffle](https://ruffle.rs) mais attend l'API de sa plateforme (KadoKado `KKApi`, Arkadeo `api.AKApi`, Frutiparc `Frusion`, CaféJeux, serveurs Muxxu…). Il faut écrire un loader ou un faux serveur qui répond à sa place.
  - **Recompilation** : seuls les graphismes (`gfx.swf`) et les sources Haxe/AS sont présents. Il faut recompiler (Haxe 2.x pour Flash 8/AVM1, Haxe 3 pour Flash 9+/AS3, MTASC pour l'AS2) avec `libs-haxe2`/`libs-haxe3`. Certaines dépendances manquent (`twinBase`, `mt.bumdum`, `../api`, `website/src/com`…) et seront à reconstituer.
  - **Portage HTML5** : jeu web dont la logique tourne sur le serveur (Hordes, DinoRPG, Mush…). Il faut réimplémenter une version solo jouable dans le navigateur à partir des sources serveur, des XML et des images.
- Tests Ruffle 0.7.1 (Chromium) : les SWF AVM1 et AS3 se chargent et s'affichent. Exemples : *Mini Fever* est jouable tel quel ; *Iceway* (standalone) tourne avec des traces de débogage ; *Cataclismo*, *Kaluga* et *Mini Troll* attendent leur API (« Connexion frusion en cours… », « format card !!! ») ; le loader KadoKado reste vide sans le fichier `gameinit.xml` côté serveur.
- Fichiers non utilisables tels quels : les `.mt` (MotionTypes, compilateur interne disparu), les `.fla` (Flash IDE, utiles seulement pour extraire des images), les `.ods` (données à convertir).

## Conventions pour chaque jeu restauré

Voir [AJOUTER-UN-JEU.md](AJOUTER-UN-JEU.md).


## KadoKado (2004-2010) : 81 jeux

Portail de mini-jeux d'arcade à score, jouables en une partie de quelques minutes.

| Jeu | Source | Techno | SWF | .hx | .as/.mt | Images | Sons | Méthode | Notes |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| ABC Revolution | `KadoKado/Games/abcrevolution` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 10 | 6 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Alchimie | `KadoKado/Games/alchimie` | MotionTypes/AS → Flash 6-8 (AVM1) | 3 | 0 | 9 | 0 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Alchimie 2 | `KadoKado/Games/alchimie2` | Haxe 2 → Flash 8 (AVM1) | 2 | 22 | 0 | 8 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Alphabounce | `KadoKado/Games/Alphabounce` | Haxe 2 → Flash 8 (AVM1) | 2 | 19 | 0 | 2 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Atlanteine | `KadoKado/Games/Atlanteine` | Haxe 2 → Flash 8 (AVM1) | 2 | 2 | 0 | 2 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Autrement | `KadoKado/Games/Autrement` | Haxe 2 → Flash 8 (AVM1) | 2 | 4 | 0 | 0 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Bactery | `KadoKado/Games/bactery` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 7 | 1 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Binary | `KadoKado/Games/Binary` | Haxe 2 → Flash 8 (AVM1) | 2 | 4 | 0 | 15 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Cerealpunk | `KadoKado/Games/cerealpunk` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 7 | 1 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Chakras | `KadoKado/Games/chakras` | Haxe 2 → Flash 8 (AVM1) | 2 | 4 | 0 | 29 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Chocomouche | `KadoKado/Games/Chocomouche` | Haxe 2 → Flash 8 (AVM1) | 2 | 3 | 0 | 8 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Cooking Lili | `KadoKado/Games/Cooking Lili` | Haxe 2 → Flash 8 (AVM1) | 2 | 11 | 0 | 7 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Corrupt | `KadoKado/Games/Corrupt` | Haxe 2 → Flash 8 (AVM1) | 2 | 9 | 0 | 0 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Cosmo Crash | `KadoKado/Games/Cosmo-Crash` | Haxe 2 → Flash 8 (AVM1) | 2 | 11 | 0 | 5 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Crepuscud | `KadoKado/Games/crepuscud` | Haxe 2 → Flash 8 (AVM1) | 2 | 8 | 0 | 0 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Cyclopean | `KadoKado/Games/Cyclopean` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 12 | 2 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Digestomax | `KadoKado/Games/Digestomax` | Haxe 2 → Flash 8 (AVM1) | 2 | 5 | 0 | 7 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Diver | `KadoKado/Games/diver` | Haxe 2 → Flash 8 (AVM1) | 3 | 5 | 0 | 0 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Dot | `KadoKado/Games/dot` | MotionTypes/AS → Flash 6-8 (AVM1) | 1 | 0 | 0 | 0 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Drakhan | `KadoKado/Games/drakhan` | MotionTypes/AS → Flash 6-8 (AVM1) | 5 | 0 | 7 | 2 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Electrolink | `KadoKado/Games/Electrolink` | Haxe 2 → Flash 8 (AVM1) | 2 | 4 | 0 | 1 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Ellon | `KadoKado/Games/ellon` | MotionTypes/AS → Flash 6-8 (AVM1) | 4 | 0 | 19 | 9 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| F1 Champion | `KadoKado/Games/f1champion` | MotionTypes/AS → Flash 6-8 (AVM1) | 3 | 0 | 4 | 12 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Flushee | `KadoKado/Games/flushee` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 5 | 25 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Fragocytoz | `KadoKado/Games/Fragocytoz` | Haxe 2 → Flash 8 (AVM1) | 3 | 8 | 0 | 4 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Happy Pty Tank | `KadoKado/Games/HappyPtyTank` | Haxe 2 → Flash 8 (AVM1) | 2 | 44 | 0 | 7 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Hexile | `KadoKado/Games/Hexile` | Haxe 2 → Flash 8 (AVM1) | 2 | 4 | 0 | 5 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Hypercube | `KadoKado/Games/hypercube` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 6 | 0 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Interwheel | `KadoKado/Games/Interwheel` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 12 | 1 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Invasion | `KadoKado/Games/invasion` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 4 | 0 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Iron Chouquette | `KadoKado/Games/Iron Chouquette` | MotionTypes/AS → Flash 6-8 (AVM1) | 6 | 0 | 14 | 14 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Judo Commando | `KadoKado/Games/Judo Commando` | Haxe 2 → Flash 8 (AVM1) | 2 | 15 | 0 | 1086 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Julianus | `KadoKado/Games/Julianus` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 7 | 4 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Kanji | `KadoKado/Games/kanji` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 6 | 1 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Kanji Gaiden | `KadoKado/Games/Kanji_Gaiden` | Haxe 2 → Flash 8 (AVM1) | 2 | 11 | 0 | 11 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Kanji Adventure | `KadoKado/Games/KanjiAdventure` | Haxe 2 → Flash 8 (AVM1) | 2 | 17 | 0 | 11 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Kanji Nightmare | `KadoKado/Games/KanjiNightmare` | MotionTypes/AS → Flash 6-8 (AVM1) | 4 | 0 | 12 | 20 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Kaskade | `KadoKado/Games/kaskade` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 6 | 1 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Kaskade 2 | `KadoKado/Games/kaskade2` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 6 | 1 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Kavern | `KadoKado/Games/kavern` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 5 | 4 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Killbulle | `KadoKado/Games/killbulle` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 7 | 2 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Kinker Surprise | `KadoKado/Games/Kinker Surprise` | Haxe 2 → Flash 8 (AVM1) | 2 | 4 | 0 | 0 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Kslash | `KadoKado/Games/kslash` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 14 | 14 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Linea | `KadoKado/Games/linea` | Haxe 2 → Flash 8 (AVM1) | 2 | 4 | 0 | 7 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Logico | `KadoKado/Games/Logico` | Haxe 2 → Flash 8 (AVM1) | 2 | 4 | 0 | 0 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Magmax | `KadoKado/Games/magmax` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 6 | 1 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Manda | `KadoKado/Games/manda` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 11 | 0 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Memopsy | `KadoKado/Games/memopsy` | MotionTypes/AS → Flash 6-8 (AVM1) | 3 | 0 | 4 | 13 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Mini-Race | `KadoKado/Games/Mini-race` | Haxe 2 → Flash 8 (AVM1) | 2 | 6 | 0 | 6 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Onu | `KadoKado/Games/onu` | Haxe 2 → Flash 8 (AVM1) | 2 | 6 | 0 | 4 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Opalus | `KadoKado/Games/Opalus` | MotionTypes/AS → Flash 6-8 (AVM1) | 3 | 0 | 9 | 0 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Opalus2 | `KadoKado/Games/Opalus2` | MotionTypes/AS → Flash 6-8 (AVM1) | 3 | 0 | 9 | 5 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Opalus Factory | `KadoKado/Games/opalusFactory` | Haxe 2 → Flash 8 (AVM1) | 2 | 5 | 0 | 7 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Oursouinvader | `KadoKado/Games/Oursouinvader` | MotionTypes/AS → Flash 6-8 (AVM1) | 5 | 0 | 10 | 1 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Pacifik | `KadoKado/Games/pacifik` | Haxe 2 → Flash 8 (AVM1) | 2 | 6 | 0 | 8 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Paradice | `KadoKado/Games/paradice` | MotionTypes/AS → Flash 6-8 (AVM1) | 4 | 0 | 12 | 4 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Pioupiou | `KadoKado/Games/pioupiou` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 8 | 1 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Pioutch | `KadoKado/Games/Pioutch` | MotionTypes/AS → Flash 6-8 (AVM1) | 3 | 0 | 2 | 0 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Popcorn | `KadoKado/Games/popcorn` | MotionTypes/AS → Flash 6-8 (AVM1) | 3 | 0 | 12 | 3 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Punchin | `KadoKado/Games/punchin` | Haxe 2 → Flash 8 (AVM1) | 2 | 5 | 0 | 0 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Puzzle Snake | `KadoKado/Games/PuzzleSnake` | Haxe 2 → Flash 8 (AVM1) | 2 | 4 | 0 | 0 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Quadrikolor | `KadoKado/Games/quadrikolor` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 7 | 2 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Razor | `KadoKado/Games/Razor` | Haxe 2 → Flash 8 (AVM1) | 2 | 4 | 0 | 33 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Red Raid | `KadoKado/Games/Red Raid` | MotionTypes/AS → Flash 6-8 (AVM1) | 5 | 0 | 20 | 2 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Safari | `KadoKado/Games/safari` | MotionTypes/AS → Flash 6-8 (AVM1) | 3 | 0 | 22 | 30 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Schizo Fuzz | `KadoKado/Games/SchizoFuzz` | Haxe 2 → Flash 8 (AVM1) | 2 | 2 | 0 | 12 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Spirale | `KadoKado/Games/Spirale` | Haxe 2 → Flash 8 (AVM1) | 2 | 5 | 0 | 15 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Sploutch | `KadoKado/Games/sploutch` | Haxe 2 → Flash 8 (AVM1) | 2 | 4 | 0 | 0 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Starfang | `KadoKado/Games/starfang` | MotionTypes/AS → Flash 6-8 (AVM1) | 0 | 0 | 12 | 12 | 0 | Recompilation | Aucun SWF compilé : recompiler les sources. |
| Superstamp | `KadoKado/Games/superstamp` | Haxe 2 → Flash 8 (AVM1) | 2 | 4 | 0 | 0 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Synapses | `KadoKado/Games/Synapses` | Haxe 2 → Flash 8 (AVM1) | 2 | 5 | 0 | 1 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Tianan Man | `KadoKado/Games/Tianan Man` | Haxe 2 → Flash 8 (AVM1) | 0 | 5 | 0 | 7 | 0 | Recompilation | Aucun SWF compilé : recompiler les sources. |
| Tortuga Qix | `KadoKado/Games/TortugaQix` | Haxe 2 → Flash 8 (AVM1) | 3 | 25 | 0 | 7 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Tout-Caen | `KadoKado/Games/Tout-Caen` | Haxe 2 → Flash 8 (AVM1) | 2 | 2 | 0 | 2 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Toymaniak | `KadoKado/Games/toymaniak` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 5 | 4 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Train | `KadoKado/Games/train` | Haxe 2 → Flash 8 (AVM1) | 2 | 12 | 0 | 119 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Travoltax | `KadoKado/Games/Travoltax` | Haxe 2 → Flash 8 (AVM1) | 2 | 18 | 0 | 3 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Tubulo | `KadoKado/Games/tubulo` | Haxe 2 → Flash 8 (AVM1) | 2 | 2 | 0 | 2 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Twin Spirit | `KadoKado/Games/TwinSpirit` | Haxe 2 → Flash 8 (AVM1) | 2 | 20 | 0 | 6 | 0 | Ruffle + API simulée | game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement. |
| Xianxiang | `KadoKado/Games/xianxiang` | MotionTypes/AS → Flash 6-8 (AVM1) | 1 | 0 | 6 | 16 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |
| Zipzap | `KadoKado/Games/zipzap` | MotionTypes/AS → Flash 6-8 (AVM1) | 2 | 0 | 5 | 0 | 0 | Ruffle + API simulée | SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement. |

## Arkadeo (2013-2014) : 16 jeux

Salle d'arcade en ligne : mini-jeux Flash AS3 à progression et objectifs.

| Jeu | Source | Techno | SWF | .hx | .as/.mt | Images | Sons | Méthode | Notes |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Animoz | `Arkadeo/games/animoz` | Haxe → Flash 10/11 (AS3) | 5 | 39 | 0 | 2 | 0 | Ruffle + API simulée | game.swf (AS3) : fournir l'API Arkadeo (api.AKApi, absente de l'archive). |
| Badabloom | `Arkadeo/games/badabloom` | Haxe → Flash 10/11 (AS3) | 12 | 12 | 0 | 68 | 0 | Ruffle + API simulée | game.swf (AS3) : fournir l'API Arkadeo (api.AKApi, absente de l'archive). |
| Battle Sheep | `Arkadeo/games/battleSheep` | Haxe → Flash 10/11 (AS3) | 2 | 6 | 0 | 52 | 0 | Ruffle + API simulée | game.swf (AS3) : fournir l'API Arkadeo (api.AKApi, absente de l'archive). |
| Brutal Teenage Crisis | `Arkadeo/games/brutal teenage crisis` | Haxe → Flash 10/11 (AS3) | 16 | 35 | 0 | 1235 | 0 | Ruffle + API simulée | game.swf (AS3) : fournir l'API Arkadeo (api.AKApi, absente de l'archive). |
| Capman | `Arkadeo/games/capman` | Haxe → Flash 10/11 (AS3) | 4 | 32 | 0 | 23 | 0 | Ruffle + API simulée | game.swf (AS3) : fournir l'API Arkadeo (api.AKApi, absente de l'archive). |
| Cataclismo | `Arkadeo/games/cataclismo` | Haxe → Flash 10/11 (AS3) | 3 | 20 | 0 | 12 | 0 | Ruffle + API simulée | game.swf (AS3) : fournir l'API Arkadeo (api.AKApi, absente de l'archive). |
| Charlotte's Quest | `Arkadeo/games/charlotteQuest` | Haxe → Flash 10/11 (AS3) | 3 | 26 | 0 | 122 | 0 | Ruffle + API simulée | game.swf (AS3) : fournir l'API Arkadeo (api.AKApi, absente de l'archive). |
| Fafi 360 | `Arkadeo/games/fafi360` | Haxe → Flash 10/11 (AS3) | 15 | 14 | 0 | 506 | 0 | Ruffle + API simulée | game.swf (AS3) : fournir l'API Arkadeo (api.AKApi, absente de l'archive). |
| Green Witch | `Arkadeo/games/greenWitch` | Haxe → Flash 10/11 (AS3) | 6 | 51 | 0 | 194 | 44 | Ruffle + API simulée | game.swf (AS3) : fournir l'API Arkadeo (api.AKApi, absente de l'archive). |
| Iceway | `Arkadeo/games/iceway` | Haxe → Flash 10/11 (AS3) | 4 | 45 | 0 | 97 | 0 | Ruffle + API simulée | game.swf (AS3) : fournir l'API Arkadeo (api.AKApi, absente de l'archive). |
| Mel | `Arkadeo/games/mel` | Haxe → Flash 10/11 (AS3) | 5 | 26 | 0 | 8 | 0 | Ruffle + API simulée | game.swf (AS3) : fournir l'API Arkadeo (api.AKApi, absente de l'archive). |
| No Sushi | `Arkadeo/games/nosushi` | Haxe → Flash 10/11 (AS3) | 1 | 12 | 0 | 5 | 0 | Ruffle + API simulée | game.swf (AS3) : fournir l'API Arkadeo (api.AKApi, absente de l'archive). |
| Overdrive | `Arkadeo/games/Overdrive` | Haxe → Flash 10/11 (AS3) | 3 | 37 | 0 | 67 | 0 | Ruffle + API simulée | game.swf (AS3) : fournir l'API Arkadeo (api.AKApi, absente de l'archive). |
| Pulsar | `Arkadeo/games/pulsar` | Haxe → Flash 10/11 (AS3) | 5 | 51 | 0 | 33 | 18 | Ruffle + API simulée | game.swf (AS3) : fournir l'API Arkadeo (api.AKApi, absente de l'archive). |
| Rock Faller (Arkadeo) | `Arkadeo/games/rockFaller` | Haxe → Flash 10/11 (AS3) | 5 | 5 | 0 | 6 | 32 | Ruffle + API simulée | game.swf (AS3) : fournir l'API Arkadeo (api.AKApi, absente de l'archive). |
| Trigo | `Arkadeo/games/trigo` | Haxe → Flash 10/11 (AS3) | 2 | 9 | 0 | 5 | 0 | Ruffle + API simulée | game.swf (AS3) : fournir l'API Arkadeo (api.AKApi, absente de l'archive). |

## CaféJeux (2007) : 13 jeux

Jeux de plateau et d'adresse en duel, joués dans un café virtuel.

| Jeu | Source | Techno | SWF | .hx | .as/.mt | Images | Sons | Méthode | Notes |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Anticorps | `CafeJeux/games/anticorps` | Haxe 2 → Flash 8 (AVM1) | 3 | 18 | 0 | 5 | 0 | Recompilation | game.swf absent (seul gfx.swf) : recompiler ; jeu à 2 joueurs : recréer l'API CaféJeux (../api absent) pour un duel local ou contre une IA. |
| Bandas | `CafeJeux/games/bandas` | Haxe 2 → Flash 8 (AVM1) | 1 | 6 | 0 | 28 | 0 | Recompilation | game.swf absent (seul gfx.swf) : recompiler ; jeu à 2 joueurs : recréer l'API CaféJeux (../api absent) pour un duel local ou contre une IA. |
| Billard | `CafeJeux/games/billard` | Haxe 2 → Flash 8 (AVM1) | 1 | 5 | 0 | 3 | 0 | Recompilation | game.swf absent (seul gfx.swf) : recompiler ; jeu à 2 joueurs : recréer l'API CaféJeux (../api absent) pour un duel local ou contre une IA. |
| Boum | `CafeJeux/games/boum` | Haxe 2 → Flash 8 (AVM1) | 2 | 7 | 0 | 0 | 0 | Ruffle + API simulée | game.swf présent ; jeu à 2 joueurs : recréer l'API CaféJeux (../api absent) pour un duel local ou contre une IA. |
| Grapiz | `CafeJeux/games/grapiz` | Haxe 2 → Flash 8 (AVM1) | 1 | 5 | 0 | 2 | 0 | Recompilation | game.swf absent (seul gfx.swf) : recompiler ; jeu à 2 joueurs : recréer l'API CaféJeux (../api absent) pour un duel local ou contre une IA. |
| Hordes (CaféJeux) | `CafeJeux/games/hordes` | Haxe 2 → Flash 8 (AVM1) | 1 | 8 | 0 | 59 | 0 | Recompilation | game.swf absent (seul gfx.swf) : recompiler ; jeu à 2 joueurs : recréer l'API CaféJeux (../api absent) pour un duel local ou contre une IA. |
| La Ferme | `CafeJeux/games/laferme` | Haxe 2 → Flash 8 (AVM1) | 2 | 5 | 0 | 10 | 0 | Ruffle + API simulée | game.swf présent ; jeu à 2 joueurs : recréer l'API CaféJeux (../api absent) pour un duel local ou contre une IA. |
| Marbils | `CafeJeux/games/marbils` | Haxe 2 → Flash 8 (AVM1) | 1 | 6 | 0 | 28 | 0 | Recompilation | game.swf absent (seul gfx.swf) : recompiler ; jeu à 2 joueurs : recréer l'API CaféJeux (../api absent) pour un duel local ou contre une IA. |
| Opalus (CaféJeux) | `CafeJeux/games/opalus` | Haxe 2 → Flash 8 (AVM1) | 1 | 5 | 0 | 0 | 0 | Recompilation | game.swf absent (seul gfx.swf) : recompiler ; jeu à 2 joueurs : recréer l'API CaféJeux (../api absent) pour un duel local ou contre une IA. |
| Paturage | `CafeJeux/games/paturage` | Haxe 2 → Flash 8 (AVM1) | 2 | 4 | 0 | 0 | 0 | Ruffle + API simulée | game.swf présent ; jeu à 2 joueurs : recréer l'API CaféJeux (../api absent) pour un duel local ou contre une IA. |
| Puissance 4 | `CafeJeux/games/power4` | Haxe 2 → Flash 8 (AVM1) | 1 | 4 | 0 | 3 | 0 | Recompilation | game.swf absent (seul gfx.swf) : recompiler ; jeu à 2 joueurs : recréer l'API CaféJeux (../api absent) pour un duel local ou contre une IA. |
| Trigolo | `CafeJeux/games/trigolo` | Haxe 2 → Flash 8 (AVM1) | 2 | 4 | 0 | 7 | 0 | Ruffle + API simulée | game.swf présent ; jeu à 2 joueurs : recréer l'API CaféJeux (../api absent) pour un duel local ou contre une IA. |
| Utopiz | `CafeJeux/games/utopiz` | Haxe 2 → Flash 8 (AVM1) | 1 | 7 | 0 | 0 | 0 | Recompilation | game.swf absent (seul gfx.swf) : recompiler ; jeu à 2 joueurs : recréer l'API CaféJeux (../api absent) pour un duel local ou contre une IA. |

## Frutiparc (2004) : 11 jeux

Le bureau virtuel de Motion Twin et ses jeux « Frusion ».

| Jeu | Source | Techno | SWF | .hx | .as/.mt | Images | Sons | Méthode | Notes |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Burning Kiwi | `Frutiparc/Games/burningKiwi` | ActionScript 1/2 → Flash 6-7 (AVM1) | 12 | 0 | 15 | 54 | 12 | Ruffle + API simulée | SWF présents ; simuler l'API Frusion (Frutiparc/frusion). |
| Frutibandas | `Frutiparc/Games/frutibandas` | ActionScript 1/2 → Flash 6-7 (AVM1) | 0 | 0 | 62 | 5 | 2 | Recompilation | Pas de SWF, sources .as + .fla : recompiler (MTASC/Haxe) ou reconstruire ; simuler l'API Frusion (Frutiparc/frusion). |
| Grapiz | `Frutiparc/Games/grapiz` | ActionScript 1/2 → Flash 6-7 (AVM1) | 0 | 0 | 32 | 7 | 0 | Recompilation | Pas de SWF, sources .as + .fla : recompiler (MTASC/Haxe) ou reconstruire ; simuler l'API Frusion (Frutiparc/frusion). |
| kaluga | `Frutiparc/Games/kaluga` | ActionScript 1/2 → Flash 6-7 (AVM1) | 18 | 0 | 68 | 338 | 2 | Ruffle + API simulée | SWF présents ; simuler l'API Frusion (Frutiparc/frusion). |
| Mini Fever | `Frutiparc/Games/miniFever` | ActionScript 1/2 → Flash 6-7 (AVM1) | 1 | 0 | 112 | 20 | 0 | Ruffle + API simulée | SWF d'origine lancé tel quel dans Ruffle (premier test). Sons, score et fin de partie à vérifier dans le thread Frutiparc. |
| Mini Troll | `Frutiparc/Games/miniTroll` | ActionScript 1/2 → Flash 6-7 (AVM1) | 3 | 0 | 113 | 650 | 0 | Ruffle + API simulée | SWF présents ; simuler l'API Frusion (Frutiparc/frusion). |
| Mini Wave 2 | `Frutiparc/Games/miniWave2` | ActionScript 1/2 → Flash 6-7 (AVM1) | 6 | 0 | 116 | 198 | 0 | Ruffle + API simulée | SWF présents ; simuler l'API Frusion (Frutiparc/frusion). |
| Motion Ball 2 | `Frutiparc/Games/motionBall2` | ActionScript 1/2 → Flash 6-7 (AVM1) | 0 | 0 | 33 | 52 | 28 | Recompilation | Pas de SWF, sources .as + .fla : recompiler (MTASC/Haxe) ou reconstruire ; simuler l'API Frusion (Frutiparc/frusion). |
| poulpi | `Frutiparc/Games/poulpi` | ActionScript 1/2 → Flash 6-7 (AVM1) | 0 | 0 | 2 | 6 | 19 | Recompilation | Pas de SWF, sources .as + .fla : recompiler (MTASC/Haxe) ou reconstruire ; simuler l'API Frusion (Frutiparc/frusion). |
| Snake 3 | `Frutiparc/Games/snake3` | ActionScript 1/2 → Flash 6-7 (AVM1) | 0 | 0 | 55 | 328 | 115 | Recompilation | Pas de SWF, sources .as + .fla : recompiler (MTASC/Haxe) ou reconstruire ; simuler l'API Frusion (Frutiparc/frusion). |
| Swapou 2 | `Frutiparc/Games/swapou2` | ActionScript 1/2 → Flash 6-7 (AVM1) | 1 | 0 | 32 | 183 | 9 | Ruffle + API simulée | SWF présents ; simuler l'API Frusion (Frutiparc/frusion). |

## Muxxu (2009-2011) : 8 jeux

Plateforme de jeux de Motion Twin : arcade, gestion et duels.

| Jeu | Source | Techno | SWF | .hx | .as/.mt | Images | Sons | Méthode | Notes |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Fever | `Muxxu/Fever` | Haxe → Flash 9 (AS3) | 24 | 173 | 0 | 210 | 0 | Ruffle + API simulée | game.swf présent (fr/en/es/de) ; simuler les appels serveur (îles, objets). |
| Snake | `Muxxu/Snake` | Haxe → Flash 9 (AS3) | 13 | 159 | 0 | 634 | 0 | Recompilation | arène game.swf à vérifier/recompiler ; cartes et quêtes à simuler. |
| Odyssey | `Muxxu/Odyssey` | Haxe → Flash 10 (AS3) | 12 | 141 | 0 | 454 | 0 | Recompilation | all.swf (graphismes) présent, client à recompiler, serveur à simuler. |
| Kube | `Muxxu/Kube` | Haxe → Flash 10/11 (AS3) | 2 | 29 | 0 | 357 | 0 | Recompilation | Monde voxel : client à recompiler, génération de monde locale. |
| Intrusion | `Muxxu/Intrusion` | Haxe 2 → Flash 8 (AVM1) | 2 | 29 | 0 | 469 | 49 | Recompilation | _gfx.swf/_cinematics.swf présents, _code.swf à recompiler. |
| La Brute | `Muxxu/LaBrute` | Haxe 2 → Flash 8 (AVM1) | 3 | 37 | 2 | 136 | 0 | Portage HTML5 | Combats calculés côté serveur : porter la simulation, réutiliser gfx.swf. |
| Kingdom | `Muxxu/Kingdom` | Haxe → Flash 9 (AS3) | 3 | 30 | 0 | 487 | 0 | Portage HTML5 | Jeu de gestion multijoueur : clients carte/bataille à recompiler, serveur à simuler. |
| CroqueMotel | `Muxxu/Hotel` | Haxe → Flash 10 (AS3) | 1 | 15 | 0 | 353 | 0 | Portage HTML5 | CroqueMotel : client à recompiler, logique de l'hôtel à simuler. |

## Jeux Motion Twin (2005-2015) : 17 jeux

Les jeux web autonomes du studio.

| Jeu | Source | Techno | SWF | .hx | .as/.mt | Images | Sons | Méthode | Notes |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Alphabounce | `Alphabounce` | Haxe 2 → Flash 8 (AVM1) | 8 | 84 | 0 | 211 | 0 | Ruffle + API simulée | Client game.swf présent ; simuler le protocole serveur (com/Protocol.hx) pour un mode solo. |
| Dinocard | `Dinocard` | MotionTypes (.mt) → Flash 7/8 | 14 | 0 | 37 | 807 | 0 | Ruffle + API simulée | code.swf/temple.swf compilés présents ; adversaire et decks à simuler côté navigateur. |
| Dinoparc | `Dinoparc` | Site web (images + XML) | 0 | 0 | 0 | 383 | 0 | Portage HTML5 | Aucun client Flash : jeu web côté serveur à réimplémenter en JS à partir des XML et images. |
| DinoRPG | `DinoRPG` | Haxe 2 serveur + clients Flash 8 | 4 | 176 | 1 | 232 | 0 | Portage HTML5 | Logique serveur (Haxe/neko) à porter en JS ; réutiliser les SWF combat/carte/donjon. |
| Galaxy 55 | `Galaxy55` | Haxe → Flash 11 (AS3) | 5 | 66 | 0 | 14 | 12 | Portage HTML5 | Alpha multijoueur : explore.swf présent, monde et serveur à simuler. |
| Hordes | `Hordes` | Haxe 2 serveur + clients Flash 8 | 16 | 83 | 2 | 60 | 0 | Portage HTML5 | Jeu de survie multijoueur côté serveur : version solo à réimplémenter, SWF carte/exploration réutilisables. |
| La Bourinette | `LaBourinette` | Haxe serveur + site | 0 | 91 | 0 | 806 | 0 | Portage HTML5 | Pas de SWF : simulation de match (src/game) à porter en JS. |
| Miniville | `Miniville` | Haxe 2 → Flash 8 (AVM1) | 2 | 4 | 0 | 2 | 0 | Ruffle + API simulée | client.swf présent ; simuler l'API serveur de la ville. |
| Monster Hotel | `MonsterHotel` | Haxe 3 + OpenFL/h3d | 0 | 114 | 0 | 96 | 209 | Recompilation | Aucun binaire : recompiler le client OpenFL en HTML5 (ou Flash puis Ruffle). |
| Mush | `Mush` | Haxe serveur + client iso AS3 | 3 | 136 | 0 | 1603 | 0 | Portage HTML5 | Jeu multijoueur côté serveur ; client iso à recompiler, partie solo à concevoir. |
| Naturalchimie 2 | `Naturalchimie2` | Haxe 2 → Flash 8 (AVM1) | 37 | 138 | 3 | 73 | 0 | Recompilation | game.swf (code) absent : recompiler fla/game/src avec gfx.swf/sound.swf. |
| Pioupiouz | `Pioupiouz` | ActionScript 2 → Flash 7/8 | 13 | 0 | 71 | 707 | 0 | Ruffle + API simulée | pioupiouz.swf/code.swf présents + niveaux XML/SQL : brancher le chargement des niveaux. |
| Rockfaller Journey | `Rockfaller` | Haxe 3 (Flash/mobile) | 1 | 89 | 0 | 279 | 81 | Recompilation | Client à recompiler (src + assets + sons) ; seul loading.swf est compilé. |
| SkyWar | `SkyWar` | Haxe 2 → Flash 8 (AVM1) | 4 | 61 | 0 | 1042 | 0 | Portage HTML5 | Stratégie multijoueur : client.swf à recompiler et serveur à simuler. |
| Socratomancie | `Socrate` | ActionScript (FLA) | 0 | 0 | 2 | 2 | 0 | Portage HTML5 | Socratomancie : boule magique ; recoder en HTML5 depuis code.as/sentence.as. |
| Teacher Story | `TeacherStory` | Haxe → Flash 11 (AS3) | 9 | 46 | 0 | 1426 | 151 | Portage HTML5 | Client classe à recompiler, logique serveur à simuler. |
| Uppercup Football | `Uppercup` | Haxe → AIR/Flash 11 | 3 | 78 | 0 | 17 | 53 | Recompilation | client.swf absent : recompiler (gfx.swf + sources), cible Flash puis Ruffle ou HTML5. |
