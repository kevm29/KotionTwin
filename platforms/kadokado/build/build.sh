#!/bin/sh
# Reconstruit platforms/kadokado/loader.swf (aucune dépendance : Python 3 suffit).
cd "$(dirname "$0")" && python3 avm1c.py loader.as ../loader.swf --width 300 --height 320 --fps 40 --bg FFFFFF --sprite "}ND*9=mt_runtime.bin"
