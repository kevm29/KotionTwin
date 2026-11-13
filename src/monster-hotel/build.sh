#!/bin/sh
# Recompile Monster Hotel (client Flash/Stage3D, mode hors ligne) pour KotionTwin.
# Prérequis : Haxe 3.4.7 dans le PATH, python3, git, et WebGamesArchives :
#   WGA=/chemin/vers/WebGamesArchives sh build.sh
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
T=$ROOT/src/mt-h3d-flash
: "${WGA:?définir WGA=chemin de WebGamesArchives}"
B=${BUILD:-/tmp/kt-monster-hotel}
FONT=${FONT:-/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf}
mkdir -p "$B"; rm -rf "$B/game" "$B/compat" "$B/gen"
LIBS="$B/libs" sh "$T/fetch-libs.sh"
cp -r "$WGA/MonsterHotel" "$B/game"
(cd "$B/game" && patch -p1 < "$HERE/kotiontwin.patch")
python3 "$ROOT/src/uppercup-football/mkcompat.py" "$WGA/libs-haxe3" "$B/compat"
mkdir -p "$B/gen" "$B/bin"; echo 1 > "$B/bin/.build"
cp "$HERE/KtMain.hx" "$B/gen/"
python3 "$T/openfl-flash/gen_assets.py" "$B/gen/KtAssets.hx" assets="$B/game/client/assets" \
  --exclude "sfx_hd/*" --exclude "music_ogg/*" --font small="$FONT" --font large="$FONT" --font roof="$FONT"
G=$B/game; L=$B/libs
cd "$B"
haxe -cp "$L/format" -cp "$L/hxsl" -cp "$L/h3d" -cp "$L/castle" -cp "$L/actuate" \
  -cp "$WGA/libs-haxe3" -cp "$G/common" -cp "$G/data" -cp "$G/client/src" -cp "$G/client/assets" -cp "$G/client" \
  -cp "$ROOT/src/mt-haxe3-compat" -cp "$B/compat" -cp "$T/mt-stubs" -cp "$T/openfl-flash" -cp "$B/gen" \
  -D h3d -D openfl --remap openfl:flash -D standalone -D prod -D NoTextureGC -D NoBGRA -D web -D kotion -D autoSave \
  -resource "$G/client/lang/fr.mo@fr" -resource "$G/client/lang/en.mo@en" -resource "$G/client/lang/de.mo@de" \
  -resource "$G/client/lang/es.mo@es" -resource "$G/client/lang/it.mo@it" -resource "$G/client/lang/pt.mo@pt" \
  -resource "$G/data/data.cdb@dataCdb" \
  -swf-version 11.6 -swf-header 800:600:30:000000 -swf "$B/client.swf" -main KtMain
mkdir -p "$ROOT/games/monster-hotel/music"
cp "$B/client.swf" "$ROOT/games/monster-hotel/client.swf"
cp "$G/sounds/music/music_intro.mp3" "$G/sounds/music/ambiant.mp3" "$G/sounds/music/music_radio1.mp3" \
   "$G/sounds/music/music_radio2.mp3" "$G/sounds/music/music_radio3.mp3" "$ROOT/games/monster-hotel/music/"
echo "OK : games/monster-hotel/client.swf"
