# Briefs des threads de restauration KotionTwin

Inventaire complet : `docs/INVENTAIRE.md` dans github.com/kevm29/KotionTwin (branche `main`). Répondre à Kevin en français.

## Socle commun à copier dans chaque brief

- Dépôt cible : `kevm29/KotionTwin` (privé). Travailler sur une branche `restore/<groupe>` et ouvrir une PR vers `main`. Le site est statique : `index.html` (catalogue), `play.html?g=<id>`, catalogue `data/games.json`.
- Source : `git clone --depth 1 https://github.com/motion-twin/WebGamesArchives` (3,4 Go, licence CC BY-NC-SA 4.0, crédits Motion Twin obligatoires, usage non commercial). Ne jamais toucher à Hammerfest.
- Lire `docs/AJOUTER-UN-JEU.md` : arborescence `games/<id>/`, code partagé dans `platforms/<plateforme>/`, sources modifiées dans `src/<id>/`, format du champ `entry`, liste de vérification.
- Ruffle 0.7.1 (`npm i @ruffle-rs/ruffle@0.7.1`, à placer dans `vendor/ruffle/`, ignoré par git ; le CDN jsDelivr est bloqué dans le conteneur). Utiliser le moteur `preferredRenderer: 'canvas'` en test headless. `tools/smoke-swf.js` et `tools/swfinfo.py` aident aux captures et à l'analyse des SWF.
- Ne modifier dans `data/games.json` que les entrées de son groupe (rebaser avant la PR, d'autres threads éditent le même fichier).
- Pour chaque jeu, avant de le passer en `"status": "jouable"` : images extraites et vérifiées non vides (JPEXS/ffdec ou dossiers bmp/gfx/img), sons et musiques qui jouent, animations à la bonne vitesse, partie jouable jusqu'au game over sans erreur console, rendu fidèle aux captures d'origine (`sc*.gif`, `teaser.jpg`, `icons/r_*`), description + commandes renseignées. Un jeu restauré partiellement reste `"en-cours"` avec une note honnête.
- Recompilation éventuelle : Haxe 2.10 pour Flash 8/AVM1 (`-swf-version 8`), Haxe 3.x pour Flash 9+/AS3 ; bibliothèques `libs-haxe2/` et `libs-haxe3/` de l'archive. Les `.mt` (MotionTypes) ne sont pas recompilables.

## Vague 1 : SWF d'origine + Ruffle (API à simuler)

### 1. KadoKado, jeux Haxe (42 jeux : Alchimie 2, Alphabounce, Atlanteine, Autrement, Binary, Chakras, Chocomouche, Cooking Lili, Corrupt, Cosmo Crash, Crepuscud, Digestomax, Diver, Electrolink, Fragocytoz, Happy Pty Tank, Hexile, Judo Commando, Kanji Gaiden, Kanji Adventure, Kinker Surprise, Linea, Logico, Mini-Race, Onu, Opalus Factory, Pacifik, Punchin, Puzzle Snake, Razor, Schizo Fuzz, Spirale, Sploutch, Superstamp, Synapses, Tianan Man, Tortuga Qix, Tout-Caen, Train, Travoltax, Tubulo, Twin Spirit)
Source `KadoKado/Games/<jeu>` + `KadoKado/Games/api` (loader.swf obfusqué, KKApi.hx, loader.v). Le loader d'origine attend `gameinit.xml` côté serveur et reste vide : écrire un loader de remplacement (`platforms/kadokado/`, Haxe 2 → Flash 8) qui charge `game.swf` et expose `KKApi` (const/val/cadd/cmult/addScore/gameOver/registerButton…, score local en localStorage via ExternalInterface ou SharedObject). Scène 300×320 (jeu 300×300 + bandeau score). Tianan Man n'a pas de SWF : recompiler. Commencer par Alphabounce et Cosmo Crash pour valider le loader.

### 2. KadoKado, anciens jeux MotionTypes/AS (39 jeux sans sources Haxe : ABC Revolution, Alchimie, Bactery, Cerealpunk, Cyclopean, Dot, Drakhan, Ellon, F1 Champion, Flushee, Hypercube, Interwheel, Invasion, Iron Chouquette, Julianus, Kanji, Kanji Nightmare, Kaskade, Kaskade 2, Kavern, Killbulle, Kslash, Magmax, Manda, Memopsy, Opalus, Opalus 2, Oursouinvader, Paradice, Pioupiou, Pioutch, Popcorn, Quadrikolor, Red Raid, Safari, Starfang, Toymaniak, Xianxiang, Zipzap)
SWF compilés (code.swf/temple.swf/gfx.swf/…) mais ancienne API KadoKado à retrouver par décompilation (JPEXS) : identifier les appels attendus du conteneur et les simuler dans le loader partagé `platforms/kadokado/` (coordonner avec le thread 1). Starfang n'a aucun SWF et Dot n'a que gfx.swf : vérifier s'ils sont récupérables.

### 3. Arkadeo (16 jeux AS3)
Source `Arkadeo/games/<jeu>`. Les `game.swf` (Flash 10/11) importent `api.AKApi`/`api.AKProtocol`, absents de l'archive (`../loader/common.dev.hxml`). Iceway a un `standalone.swf` qui tourne déjà dans Ruffle (avec traces de debug « Game.hx:350 » à masquer). Écrire un hôte AS3 (Haxe 3) qui fournit AKApi (modes, niveaux, score, objectifs « kdo »), ou recompiler en mode standalone. No Sushi et Capman n'ont pas de game.swf : recompiler. Vérifier les sons (greenWitch, pulsar, rockFaller).

### 4. Frutiparc (11 jeux AS1/AS2)
Source `Frutiparc/Games/<jeu>` + `Frutiparc/frusion` (API Frusion). Mini Fever est déjà jouable tel quel (`games/fp-minifever/`, à vérifier en entier : sons, fin de partie, taille de scène 281×281). Kaluga affiche « Connexion frusion en cours… », Mini Troll « format card !!! » : simuler le serveur Frusion. Frutibandas, Grapiz, Motion Ball 2, Poulpi, Snake 3, Swapou 2 n'ont pas de SWF : recompiler depuis .as/.fla (MTASC) ou reconstruire ; beaucoup de sons mp3 à brancher.

### 5. CaféJeux (13 jeux de duel)
Source `CafeJeux/games/<jeu>` + `CafeJeux/bitmaps`. `../api/params.hxml` et l'API réseau manquent. Seuls Boum, La Ferme, Pâturage, Trigolo ont un game.swf ; les 9 autres (Anticorps, Bandas, Billard, Grapiz, Hordes, Marbils, Opalus, Puissance 4, Utopiz) n'ont que gfx.swf : recompiler en Haxe 2. Recréer l'API CaféJeux pour jouer à deux en local (hotseat) et, si possible, contre une IA simple.

### 6. Jeux Flash 8 autonomes : Alphabounce, Miniville, Pioupiouz, Dinocard
Alphabounce : `web/swf/game.swf` + `com/Protocol.hx` → simuler le serveur (missions, zones, inventaire) pour un mode solo. Miniville : `client/swf/client.swf`, simuler l'API de la ville. Pioupiouz : `game/swf/pioupiouz.swf` + niveaux `levels/*.xml|sql`. Dinocard : `client/swf/code.swf`/`temple.swf` (sources .mt non recompilables), simuler adversaire et decks.

## Vague 2 : recompilation

### 7. Muxxu arcade : Fever, Snake, Kube, Odyssey, Intrusion
Fever : `www/swf/<langue>/game.swf` présent (AS3) : simuler les réponses serveur (îles, objets). Snake, Odyssey, Kube, Intrusion : recompiler les clients (Haxe 3 / Haxe 2 pour Intrusion), dépendances `../base/com` et `bumdum` à reconstituer, puis simuler le serveur.

### 8. Haxe 3 récents : Naturalchimie 2, Rockfaller Journey, Uppercup Football, Monster Hotel
Naturalchimie 2 : recompiler `fla/game/src` avec `gfx.swf`/`sound.swf`. Rockfaller : client Haxe 3 + assets/sons (www/sounds). Uppercup : `uppercup.hxml` (cible AIR) vers Flash ou HTML5. Monster Hotel : OpenFL + h3d, recompiler en HTML5 ; 209 sons.

## Vague 3 : portages de jeux serveur (un thread par ligne)

9. **Hordes** : survie multijoueur ; porter la logique (`src/*.hx`, xml) en version solo JS, réutiliser `fla/map` et `fla/exploration`.
10. **DinoRPG** : porter la logique serveur (Dino.hx, Script.hx, xml) ; réutiliser les SWF combat/carte/donjon.
11. **Mush** : jeu multijoueur complexe ; recompiler le client iso et concevoir une partie solo.
12. **La Brute + Kingdom + CroqueMotel (Muxxu)** : simulations serveur à porter, clients Flash 8/AS3 à réutiliser.
13. **SkyWar + Galaxy55** : stratégie/exploration multijoueur, mode solo à concevoir.
14. **La Bourinette + Teacher Story** : simulations de match / de classe à porter en JS.
15. **Dinoparc + Socratomancie** : Dinoparc n'a pas de client Flash (images + XML) → réimplémentation HTML5 ; Socratomancie (boule magique, `code.as`, `sentence.as`) → petit portage HTML5.

## Site web (en parallèle)

16. **Interface du site** : le squelette existe (catalogue filtrable, page de jeu Ruffle/HTML5). À faire : activation de GitHub Pages, vignettes manquantes (103 jeux sans capture : générer depuis le gfx.swf ou un écran titre), pages de collection, sauvegarde des scores en localStorage, mode plein écran et mobile, accessibilité. Ne pas toucher aux entrées de jeux de `data/games.json`.
