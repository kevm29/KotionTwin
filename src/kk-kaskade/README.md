# Kaskade : reconstruction du SWF final

L'archive ne contient pas `swf/kaskade.swf`, seulement `swf/code.swf` (code MotionTypes compilé, non obfusqué) et `swf/gfx.swf` (graphismes).
`merge_swf.py` refait ce que faisait `swfmake.xml` : il reprend toutes les définitions du gfx, ajoute le symbole exporté `code` (renuméroté après le dernier identifiant du gfx) et écrit un SWF Flash 8 compressé.

```
python3 src/kk-kaskade/merge_swf.py <archive>/KadoKado/Games/kaskade/swf/code.swf <archive>/KadoKado/Games/kaskade/swf/gfx.swf games/kk-kaskade/kaskade.swf
```

Différence avec l'original : pas d'obfuscation, donc le loader doit exposer `KKApi`, `Manager`, `init`, `main` et le symbole `code` sous leur nom clair.
