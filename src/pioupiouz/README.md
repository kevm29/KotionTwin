# Pioupiouz

Rebâtir : `python3 -I src/pioupiouz/build.py <WebGamesArchives>/Pioupiouz` (ajouter `KT_DEBUG=1` pour des traces).

Voir l'en-tête de `build.py` : réparation de la table d'obfuscation de `temple.swf` (noms natifs
rétablis en alignant `code.swf` et `pioupiouz.swf`), ajout de `StdInc` et d'un démarreur AVM1
assemblé avec `tools/avm1.py`, conversion de `levels.sql` en `games/pioupiouz/levels/*.xml`.
