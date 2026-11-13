# Capman (Arkadeo) : port Haxe 3

L'archive ne contient que les sources Haxe 2 (et les ressources graphiques), pas de `game.swf`.
Haxe 2.10 n'étant plus téléchargeable, les sources ont été portées en Haxe 3.4.7 :

- `src/` : sources du jeu (Arkadeo/games/capman/src), converties mécaniquement
  (`extends A, implements B`, `callback()` → `.bind()`, `Hash` → `Map`, `haxe.Public` → `@:publicFields`,
  typedefs `{> MC, …}` → `Dynamic`) puis corrigées à la main là où le compilateur le demandait ;
- `lib/` : bibliothèques Motion Twin de `libs-haxe2/mt` réellement utilisées, converties de la même façon ;
- `stub/` : ce qui manquait dans l'archive. `api/AKApi.hx` et `api/AKProtocol.hx` réécrivent l'API
  Arkadeo pour déléguer à l'hôte (`platforms/arkadeo/host.swf`), `game/IGame.hx`, `mt/flash/Volatile.hx`
  (simple alias), et pour Capman `mt/MLib.hx` et `mt/Std.hx` ;
- `res/` : SWF de ressources d'origine liés à la compilation (`-swf-lib`).

Recompiler (depuis ce dossier) : `haxe build.hxml` → `games/ak-capman/game.swf`.
