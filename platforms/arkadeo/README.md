# Hôte Arkadeo

Les jeux Arkadeo (2013-2014) sont des SWF AS3 compilés en Haxe. Chaque `game.swf` contient
une classe façade `api.AKApi` (renommée `api_.AKApi_` par l'obfuscateur de Motion Twin) dont
toutes les méthodes délèguent à un objet statique `AKApi_.api_`, fourni à l'origine par le
chargeur du site arkadeo.com. Ce chargeur n'est pas dans l'archive.

`host.swf` (sources dans `src/Host.hx`, Haxe 3.4.7) le remplace :

1. il charge `game.swf` dans un domaine d'application neuf (FlashVar `game`, relative à `base`) ;
2. avant l'initialisation statique du jeu, il installe dans `AKApi_.api_` (ou `api.AKApi.api`
   pour les jeux recompilés par KotionTwin) un objet qui implémente l'interface attendue,
   avec les noms obfusqués suffixés par « _ » : `getSeed_`, `getGameMode_`, `getLevel_`,
   `const_`/`aconst_` (entiers « sécurisés » avec `get_`/`add_`/`set_`), `addScore_`, `getScore_`,
   `gameOver_`, `setProgression_`, `isDown_`/`isToggled_` (clavier), `isClicked_` (bouton de
   souris enfoncé), `emitEvent_`/`getEvent_` (file d'événements rejouée à l'image suivante),
   `getInGamePrizeTokens_`/`takePrizeTokens_` (kdo), `saveState_`/`getState_`,
   `setStatusText_`/`setStatusMC_` (barre d'état), `waitEngine_`/`engineReady_`, etc. ;
3. il instancie la classe `Game_` (ou `Game`), l'ajoute à la scène et appelle `update_(true)`
   à chaque image, à la cadence d'origine du jeu ;
4. il affiche un menu (Ligue = score à battre, Progression = niveaux à débloquer), une barre
   d'état de 20 px sous la zone de jeu (600×460) et un écran de fin de partie.
   Record et niveaux débloqués sont gardés dans un SharedObject (localStorage avec Ruffle).
   Les `trace()` de debug des jeux sont redirigées vers la console.

FlashVars : `game` (défaut `game.swf`), `title`, `id` (clé de sauvegarde), `levels` (nombre de
niveaux en Progression, défaut 20), `modes` (`both`, `league` ou `progression`).

Entrée type dans `data/games.json` :

```json
"entry": { "type": "ruffle", "swf": "platforms/arkadeo/host.swf", "width": 600, "height": 480,
  "base": "games/ak-trigo/", "flashvars": { "game": "game.swf", "title": "Trigo", "id": "ak-trigo" },
  "config": { "preferredRenderer": "wgpu-webgl" } }
```

Le moteur `wgpu-webgl` (ou `webgpu`) est nécessaire : plusieurs jeux utilisent
`BitmapData.draw`, que les moteurs `webgl` et `canvas` de Ruffle 0.7.1 ne gèrent pas.

## Recompiler l'hôte

```sh
haxe build.hxml        # Haxe 3.4.7, produit host.swf (SWF 21 pour exposer JSON aux jeux Flash 11)
```

## Retouches de jeux

- `patches/greenwitch_sfx.py` : Green Witch avait été compilé avec `-D disableSfx`. Le corps de
  `mt.deepnight.Sfx.start()` est réécrit dans le bytecode (outil `tools/abc_patch.py`), puis les
  sons d'origine sont réinjectés avec `tools/swf_add_sounds.py` :

  ```sh
  python3 platforms/arkadeo/patches/greenwitch_sfx.py <archive>/Arkadeo/games/greenWitch/swf/game.swf /tmp/gw.swf
  cd <archive>/Arkadeo/games/greenWitch/sounds
  python3 tools/swf_add_sounds.py /tmp/gw.swf games/ak-greenwitch/game.swf $(for f in *.wav *.mp3; do echo "_SFX_${f%.*}=$PWD/$f"; done)
  ```
- No Sushi et Capman n'ont pas de `game.swf` dans l'archive : voir `src/ak-nosushi` et `src/ak-capman`.

`tools/abcdump.py` désassemble l'ABC d'un SWF (classes, méthodes, bytecode) : c'est lui qui a
permis de retrouver l'interface de `AKApi` sans décompilateur Java.
