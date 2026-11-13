# Anciens jeux KadoKado (MotionTypes)

35 des 39 jeux KadoKado « première époque » (compilés avec MotionTypes, sans sources Haxe) tournent avec leur SWF d'origine dans `games/kk-<id>/`, lancés par le loader commun `platforms/kadokado/loader.swf` avec la FlashVar `mt=1`.

## Ce qu'il a fallu comprendre

- Les SWF finaux sont obfusqués par un hachage déterministe commun à tous les jeux et à `api/loader.swf` : `KKApi` = `;ndCG`, `Manager` = `980Sb`, `init` = `}-B2`, `main` = `0D 6`, symbole de code `code` = `90D*`. La table complète a été obtenue en alignant `swf/code.swf` (non obfusqué) et le SWF final de 11 jeux (`pairmap.py`), elle est dans `src/kk-kaskade/obfmap.json`.
- Le code du jeu est dans un symbole exporté (`90D*`) que le loader attache, puis il appelle `Manager.init(clip)` et `Manager.main()` à chaque image.
- La bibliothèque d'exécution MotionTypes (`Std`, `Log`…) n'est pas dans les jeux : elle était fournie par le sprite 1 du loader d'origine. Le loader KotionTwin la réinjecte telle quelle (`platforms/kadokado/build/mt_runtime.bin`).
- Aucun de ces jeux n'avait de son (aucun DefineSound dans les SWF).

## Outils

- `avm1dump.py fichier.swf` : désassembleur AVM1 minimal (pools de constantes, fonctions, exports).
- `pairmap.py code.txt final.txt` : aligne deux désassemblages pour retrouver les noms obfusqués.
- `swfassets.py sortie/ fichier.swf…` : extrait les bitmaps en PNG, vérifie qu'ils ne sont ni vides ni transparents, liste les sons.

## Jeux non récupérables en l'état

Dot (gfx.swf seul), Kslash, Starfang et Xianxiang (sources `.mt` sans SWF de code : le compilateur MotionTypes n'existe plus) ne peuvent revenir que par une réécriture.
