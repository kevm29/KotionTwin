#!/bin/sh
# Recompile Naturalchimie 2 (client Flash 8) pour KotionTwin.
# Usage : WGA=/chemin/vers/WebGamesArchives HAXE2=/chemin/haxe-2.07 sh build.sh
# HAXE2 : dossier d'une installation Haxe 2.07 (bin haxe + std), voir README.md.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
WGA=${WGA:?WGA = chemin du dépôt WebGamesArchives}
HAXE2=${HAXE2:?HAXE2 = dossier Haxe 2.07 (contient usr/bin/haxe)}
OUT="$REPO/games/naturalchimie-2"
W=$(mktemp -d)

# 1. Sources du jeu + correctifs KotionTwin
cp -r "$WGA/Naturalchimie2/fla" "$WGA/Naturalchimie2/src" "$W/"
(cd "$W" && patch -p1 -s < "$HERE/kotiontwin.patch")

# 2. Code (Haxe 2.07, Flash 8). Les bouchons (faux serveur, mt.net.Codec, mt.Timer) passent en dernier = prioritaires.
export HAXE_LIBRARY_PATH="$HAXE2/usr/share/haxe/std"
"$HAXE2/usr/bin/haxe" -swf "$W/code.swf" -swf-version 8 -swf-header 300:356:40:000000 -D no-swf-compress \
  -main Loader --flash-strict \
  -cp "$W/fla/game/src" -cp "$W/fla/game/src/mode" -cp "$W/fla/game/src/artefact" -cp "$W/fla/lib" \
  -cp "$W/src/com" -cp "$WGA/libs-haxe2" -cp "$HERE/stubs"

# 3. Assemblage avec les graphismes, la bibliothèque des persos et les 17 bruitages (comme swfmake)
mkdir -p "$OUT/swf"
python3 "$REPO/tools/swfmerge.py" "$W/code.swf" "$OUT/game.swf" \
  "$W/fla/game/swf/gfx.swf" "$W/fla/persos/swf/display_lib.swf" "$W/fla/game/swf/sound.swf"

# 4. objectMc.swf (dessins des éléments et artefacts) : l'original n'existe qu'en .fla.
#    On prend le symbole « object » de la version KadoKado (même structure smc/gotoAndStop)
#    et on ajoute la fonction _set de persos/library/objectCode.as.
python3 "$REPO/tools/as1c.py" "$HERE/objroot.as" "$W/objroot.swf" --width 48 --height 55 --fps 12 --version 8
python3 "$REPO/tools/swfmerge.py" "$W/objroot.swf" "$OUT/swf/objectMc.swf" "$WGA/KadoKado/Games/alchimie2/swf/gfx.swf"

rm -rf "$W"
echo "OK : $OUT/game.swf et $OUT/swf/objectMc.swf"
