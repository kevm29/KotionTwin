#!/bin/sh
# Recompile les jeux CaféJeux (Haxe 2.10 -> Flash 8 / AVM1) avec l'API recréée.
#
#   HAXE=/chemin/haxe HAXE_LIBRARY_PATH=/chemin/std WGA=/chemin/WebGamesArchives \
#     sh platforms/cafejeux/build.sh [jeu ...]
#
# Pour chaque jeu <g> : sources src/cj-<g>/, graphismes $WGA/CafeJeux/games/<g>/swf/gfx.swf
# (copiés dans src/cj-<g>/), sortie games/cj-<g>/game.swf (300×300, 40 i/s).
set -e
cd "$(dirname "$0")/../.."
HAXE=${HAXE:-haxe}
WGA=${WGA:-../WebGamesArchives}
GAMES=${*:-"anticorps bandas billard boum grapiz hordes laferme opalus paturage power4 trigolo utopiz"}
for g in $GAMES; do
  out=games/cj-$g
  mkdir -p "$out"
  [ -f "src/cj-$g/gfx.swf" ] || cp "$WGA/CafeJeux/games/$g/swf/gfx.swf" "src/cj-$g/gfx.swf"
  libs="-swf-lib src/cj-$g/gfx.swf"
  # Anticorps assemble aussi bumdum.swf (voir swfmake.xml d'origine)
  if [ "$g" = anticorps ]; then
    [ -f "src/cj-$g/bumdum.swf" ] || cp "$WGA/CafeJeux/games/$g/swf/bumdum.swf" "src/cj-$g/bumdum.swf"
    libs="$libs -swf-lib src/cj-$g/bumdum.swf"
  fi
  echo "== $g"
  "$HAXE" -swf "$out/game.swf" -swf-version 8 -swf-header 300:300:40:FFFFFF \
    $libs -main Main \
    -cp platforms/cafejeux/api -cp "src/cj-$g" -cp platforms/cafejeux/lib \
    Game
done
