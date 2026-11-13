#!/bin/sh
# Recompile Uppercup Football (client Flash) pour KotionTwin.
# Prérequis : Haxe 3.4.7 dans le PATH, python3, et une copie de WebGamesArchives :
#   WGA=/chemin/vers/WebGamesArchives sh build.sh
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
: "${WGA:?définir WGA=chemin de WebGamesArchives}"
B=${BUILD:-/tmp/kt-uppercup}
rm -rf "$B"; mkdir -p "$B"
cp -r "$WGA/Uppercup" "$B/game"
(cd "$B/game" && patch -p1 < "$HERE/kotiontwin.patch")
python3 "$HERE/mkcompat.py" "$WGA/libs-haxe3" "$B/compat"
cd "$B/game"
haxe \
  -cp "$WGA/libs-haxe3" -cp src -cp . -cp assets -cp "$HERE/stubs" \
  -cp "$ROOT/src/mt-haxe3-compat" -cp "$B/compat" \
  -swf "$B/client.swf" -swf-header 600:600:30:FFFFFF -swf-version 11.3 -main Main \
  -swf-lib assets/gfx.swf --flash-strict \
  -D spriteParticles -D standalone -D noShareANE -D prod -D v105 -D v110 -D kotion \
  -resource texts.fr.xml@fr -resource texts.en.xml@en -resource texts.es.xml@es \
  -resource texts.hu.xml@hu -resource texts.pt.xml@pt -resource texts.ru.xml@ru \
  -resource texts.tr.xml@tr -resource texts.it.xml@it -resource texts.de.xml@de \
  -resource teams.xml@teams
cp "$B/client.swf" "$ROOT/games/uppercup-football/client.swf"
echo "OK : games/uppercup-football/client.swf"
