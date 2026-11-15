#!/bin/sh
# Recompile les jeux CaféJeux (Haxe 2 -> Flash 8 / AVM1) avec hxc, le compilateur maison de
# KotionTwin (platforms/cafejeux/hxc), et l'API CaféJeux recréée (platforms/cafejeux/api).
#
#   WGA=/chemin/WebGamesArchives sh platforms/cafejeux/build.sh [jeu ...]
#
# Pour chaque jeu <g> : sources src/cj-<g>/, graphismes $WGA/CafeJeux/games/<g>/swf/gfx.swf
# (copiés dans src/cj-<g>/), sortie games/cj-<g>/game.swf (300×300, 40 i/s). Python 3 suffit.
set -e
cd "$(dirname "$0")/../.."
WGA=${WGA:-../WebGamesArchives}
GAMES=${*:-"anticorps bandas billard boum grapiz hordes laferme opalus paturage power4 trigolo utopiz"}
for g in $GAMES; do
  mkdir -p "games/cj-$g"
  [ -f "src/cj-$g/gfx.swf" ] || cp "$WGA/CafeJeux/games/$g/swf/gfx.swf" "src/cj-$g/gfx.swf"
  libs="-lib src/cj-$g/gfx.swf"
  # Anticorps assemble aussi bumdum.swf (voir swfmake.xml d'origine)
  if [ "$g" = anticorps ]; then
    [ -f "src/cj-$g/bumdum.swf" ] || cp "$WGA/CafeJeux/games/$g/swf/bumdum.swf" "src/cj-$g/bumdum.swf"
    libs="$libs -lib src/cj-$g/bumdum.swf"
  fi
  python3 platforms/cafejeux/hxc/hxc.py -cp platforms/cafejeux/hxc/std -cp platforms/cafejeux/api \
    -cp "src/cj-$g" -cp platforms/cafejeux/lib -main Main $libs -o "games/cj-$g/game.swf" \
    --size 300x300 --fps 40 Game
done
