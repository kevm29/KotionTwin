# Snake (Muxxu) — restauration KotionTwin

Source : `Muxxu/Snake/clients/arene` de WebGamesArchives (Haxe → Flash 9, 800×420).

Le `swf/game.swf` de l'archive a été compilé avec `-D dev` (voir `game.hxml`) : en mode
`browser`, il remplace les données du serveur par 200 cartes au hasard, ouvre l'écran de
tournoi (draft) au lieu du choix de cartes, et le bouton « rejouer » pointe vers un fichier
local du développeur. Les dépendances de recompilation (`base/com`, `bumdum/old_lib`) ne
sont pas dans l'archive, d'où une retouche du bytecode plutôt qu'une recompilation.

`patch_game.py game.swf games/mx-snake/game.swf` (outils `tools/abc_patch.py` et
`tools/abcdump.py`) :

1. `Main.main` : un `jump` saute le bloc `#if dev` du mode browser ; les données et
   l'adresse `dom` viennent alors des flashvars.
2. `Game.sendInfos` : `ExternalInterface.call("ktSnakeEnd", score)` ajouté en tête
   (fin de partie), pour enregistrer le score sur le site.
3. `Game.toggleReplay` (touche S de debug) vidé : sinon la fin de partie enregistre un
   replay dans un SharedObject au lieu d'afficher le bilan.

La fin de partie reste celle du mode dev : pas d'appel serveur `/end`, progression
« Encyclopéfruit » tirée au hasard au bilan.

## Données fournies par `games/mx-snake/index.html`

`Codec.getData("data")` accepte un mode « FAKE » : si la chaîne commence par la clé `k`,
le reste est lu comme une sérialisation `haxe.Serializer` en clair (avec
`USE_ENUM_INDEX`). La page envoie un `_DataBrowser` :
`{_age, _plays, _cards:[{_type:_CardType(i), _available:true}…], _draft:null, _me}` avec
les 131 cartes de `data.ods` (feuille « cartes »). `_plays` est compté en localStorage
(l'aide au choix des cartes s'affiche pendant les 16 premières parties). `time` = heure
courante en ms, `dom = javascript:ktSnakeAgain()` relance le lecteur.
