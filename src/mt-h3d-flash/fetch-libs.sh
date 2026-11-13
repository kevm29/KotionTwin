#!/bin/sh
# Récupère les bibliothèques Haxe de l'époque (fin 2015) aux révisions utilisées par KotionTwin,
# et applique les correctifs KotionTwin au moteur h3d de Motion Twin.
# usage : LIBS=/chemin/vers/dossier sh fetch-libs.sh
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
: "${LIBS:?définir LIBS=dossier de destination}"
mkdir -p "$LIBS"; cd "$LIBS"
get() { # nom url révision
  [ -d "$1" ] || git clone -q "$2" "$1"
  git -C "$1" am --abort 2>/dev/null || true
  git -C "$1" checkout -q -f "$3"
}
get h3d      https://github.com/motion-twin/h3d.git     6215b81940ceac84314693d2a7ae97803032e952  # branche h3d_mt (déc. 2015)
get hxsl     https://github.com/motion-twin/hxsl.git    74a7dfffe9de845476ef05009ac8d0d707749fe3
get format   https://github.com/HaxeFoundation/format.git b42f57c97e61be7bba215cb4a2aea9c18b1a41ba
get castle   https://github.com/ncannasse/castle.git    147dd02eb315530474364b958905f5815a98798a
get actuate  https://github.com/jgranick/actuate.git    242691f28a5ffd6e14a93ed8acba1f375972ac3b
cd h3d && git -c user.name=kt -c user.email=kt@localhost am -q --keep-cr "$HERE"/patches/*.patch
echo "OK : bibliothèques prêtes dans $LIBS"
