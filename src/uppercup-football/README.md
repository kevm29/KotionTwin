# Uppercup Football (2014) — recompilation Flash

Le dépôt d'origine (`WebGamesArchives/Uppercup`) contient les sources Haxe et `assets/gfx.swf`, mais pas
`client.swf` : le jeu visait AIR (Android/iOS). On le recompile ici en SWF Flash 11.3 joué par Ruffle.

```sh
WGA=/chemin/vers/WebGamesArchives sh build.sh     # Haxe 3.4.7 dans le PATH
```

Ce que fait `build.sh` :

1. copie `Uppercup/` et applique `kotiontwin.patch` (modifications du jeu, toutes sous `#if kotion`
   ou équivalent) :
   - achats intégrés (`m/IapMan.hx`) remplacés par un bouchon : jeu complet débloqué ;
   - sauvegarde via `SharedObject` au lieu du `SecureSO` chiffré d'AIR ;
   - `NativeApplication` (AIR) remplacé par la scène Flash ; boutons Twitter/Facebook/« Nos jeux »/Twinoid retirés ;
   - score envoyé au site (`ktSubmitScore`) = total des étoiles, à chaque amélioration.
2. génère `compat/` avec `src/mt-haxe3-compat/mkcompat.py` : la bibliothèque `libs-haxe3` de l'archive est plus récente que le jeu
   (2015-2016). Le script en copie quelques classes en y rajoutant l'API de 2014 (`Cooldown.set`, `Delayer.add`,
   `Tweenie.create`, `BSprite.setCenter`, gestion globale de `FParticle`, `Process` de 2014…).
3. ajoute `stubs/` (Google Analytics, Chartboost, SecureSO) et `src/mt-haxe3-compat` (`mt.MLib`,
   `mt.flash.Volatile`, absentes de l'archive et reconstituées).

Les 53 sons d'`assets/sfx` sont intégrés au SWF par la macro `Sfx.importDirectory`.
