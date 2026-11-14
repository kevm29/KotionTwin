#!/usr/bin/env python3
"""Ajoute en tête de games/alphabounce/game.swf un petit code AVM1 qui remplace
BitmapData.prototype.colorTransform par l'équivalent ColorMatrixFilter + applyFilter.

Pourquoi : les effets « plasma » d'Alphabounce (traînées de la balle, explosions) font à chaque
image applyFilter (calculé sur la carte graphique par Ruffle), colorTransform (calculé par le
processeur) puis draw (carte graphique). Chaque colorTransform force Ruffle à rapatrier l'image
de la carte graphique puis à la renvoyer : le jeu rame dès qu'un effet tourne. Avec un filtre
de matrice de couleurs, tout reste sur la carte graphique ; le résultat est le même.

    python3 -I src/alphabounce/gpu_colortransform.py games/alphabounce/game.swf
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import avm1
from avm1 import Asm

MARK = 'ktGpuColorTransform'

def code():
    f = Asm()
    # new flash.filters.ColorMatrixFilter([...20 coefficients...])
    m = ['ct.redMultiplier', 0, 0, 0, 'ct.redOffset',
         0, 'ct.greenMultiplier', 0, 0, 'ct.greenOffset',
         0, 0, 'ct.blueMultiplier', 0, 'ct.blueOffset',
         0, 0, 0, 'ct.alphaMultiplier', 'ct.alphaOffset']
    def matrix(a):
        for v in reversed(m):
            a.get(v) if isinstance(v, str) else a.push(v)
        a.push(len(m)).op('InitArray')
    def cmf(a):
        matrix(a); a.push(1); a.get('flash.filters'); a.push('ColorMatrixFilter').op('NewMethod')
    def point(a):
        a.get('rect.y'); a.get('rect.x'); a.push(2); a.get('flash.geom'); a.push('Point').op('NewMethod')
    # this.applyFilter(this, rect, new Point(rect.x, rect.y), filtre)
    f.call('this.applyFilter', lambda a: a.get('this'), lambda a: a.get('rect'), point, cmf)
    a = Asm()
    a.set('flash.display.BitmapData.prototype.colorTransform', lambda s: s.func('', ['rect', 'ct'], f))
    a.set(f'_global.{MARK}', lambda s: s.push(True))
    return a

path = sys.argv[1]
swf = avm1.read_swf(path)
if any(c == 12 and MARK.encode() in d for c, d in swf['tags']):
    print('déjà patché'); sys.exit(0)
# avant le premier tag d'action ou de fin d'image
i = next(k for k, (c, d) in enumerate(swf['tags']) if c in (1, 12, 59))
swf['tags'].insert(i, avm1.do_action(code()))
avm1.write_swf(path, swf)
print('colorTransform → ColorMatrixFilter ajouté à', path)
