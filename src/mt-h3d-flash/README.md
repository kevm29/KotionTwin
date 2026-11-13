# Chaîne de compilation h3d (Motion Twin, 2015) → SWF Flash 11 joué par Ruffle

Monster Hotel et Rockfaller Journey utilisent OpenFL + le moteur **h3d** de Motion Twin (branche `h3d_mt`
du dépôt public `motion-twin/h3d`, fin 2015), qui affiche tout en Stage3D. On compile la cible **Flash**
avec Haxe 3.4.7, sans l'outil `lime`/`openfl` :

- `fetch-libs.sh` : clone h3d, hxsl, format, castle, actuate aux révisions de l'époque et applique `patches/`
  (constantes Stage3D remplacées par leurs chaînes, car Ruffle n'a pas les classes `Context3DBufferUsage`…,
  et quelques ajustements pour Haxe 3.4).
- `openfl-flash/` : remplaçant minimal d'`openfl.Assets` pour la cible Flash (`--remap openfl:flash`),
  et `gen_assets.py`, qui intègre au SWF les images, XML, JSON et polices d'un dossier d'assets.
- `mt-stubs/` : classes de la bibliothèque Motion Twin absentes de l'archive, reconstituées ou neutralisées
  (`mt.net.Codec`, `mt.device.*`, `mt.Worker`, `mt.Assets`, `mt.Console`…).
- La compatibilité avec l'API 2014-2015 de `libs-haxe3` est générée par `src/mt-haxe3-compat/mkcompat.py`.

Ruffle doit utiliser le moteur `wgpu-webgl` (Stage3D).
