#!/usr/bin/env python3
"""Reconstruit games/pioupiouz/ à partir de l'archive WebGamesArchives.

    python3 -I src/pioupiouz/build.py <chemin>/WebGamesArchives/Pioupiouz

1. temple.swf (version web, toutes les tuiles et décors) est complété par :
   - la bibliothèque StdInc (copiée depuis pioupiouz.swf, même table d'obfuscation) ;
   - un code de démarrage qui remplace le chargeur du site d'origine : il définit les
     fonctions globales attendues (loadLevel / startGame / exitGame / saveLevel, noms
     obfusqués retrouvés en alignant code.swf et temple.swf), lance Manager.init puis
     Manager.main à chaque image.
2. levels/levels.sql (niveaux officiels + tutoriels) est converti en un fichier XML par
   niveau, au format attendu par Game.onLevelLoaded, et en un catalogue levels.json.
"""
import sys, os, json, re
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import avm1, swfdis
from avm1 import Asm, UNDEF

SRC = sys.argv[1] if len(sys.argv) > 1 else '../WebGamesArchives/Pioupiouz'
OUT = os.path.join(ROOT, 'games', 'pioupiouz')
os.makedirs(os.path.join(OUT, 'levels'), exist_ok=True)

# ---------------------------------------------------------------- table d'obfuscation
def main_pool(path):
    body, p = swfdis.load(path); bl = []
    swfdis.walk(body, p, len(body), 'root', bl)
    best = []
    for t, code in bl:
        if code and 'Export' not in t and 'Import' not in t:
            pool = swfdis.dis(code, [])
            if len(pool) > len(best): best = pool
    return best
clear = main_pool(f'{SRC}/game/swf/code.swf')
obf = main_pool(f'{SRC}/game/swf/temple.swf')
assert len(clear) == len(obf), 'pools non alignés'
# temple.swf a été obfusqué sans la liste des noms natifs de Flash (prototype, Array,
# getBounds, _x…) : il ne peut pas fonctionner tel quel. pioupiouz.swf (version
# autonome) a été obfusqué avec le même dictionnaire mais en protégeant ces noms :
# tout nom resté en clair dans pioupiouz.swf est donc rétabli en clair dans temple.swf.
protected = set(main_pool(f'{SRC}/game/swf/pioupiouz.swf'))
fixed_pool = [c if (c in protected and c != b) else b for c, b in zip(clear, obf)]
print(sum(1 for x, y in zip(fixed_pool, obf) if x != y), 'noms natifs rétablis')
O = dict(zip(clear, fixed_pool))
def o(name): return O.get(name, name)
# StdInc n'est pas dans code.swf : noms relevés dans pioupiouz.swf (frame 3 : _global.StdInc.init())
STDINC, STDINC_INIT = ';7pIo', o('init')

# ---------------------------------------------------------------- StdInc
std = avm1.read_swf(f'{SRC}/game/swf/pioupiouz.swf')
stdinc = None
for c, d in std['tags']:
    if c == 59:
        stdinc = d[2:]   # DoInitAction : u16 id du sprite puis le code
assert stdinc

# ---------------------------------------------------------------- code de démarrage
EI = 'flash.external.ExternalInterface'
DEBUG = os.environ.get('KT_DEBUG')
def dbg(asm, msg):
    if DEBUG: asm.push(msg).Trace()
a = Asm()
dbg(a, 'boot: stdinc')
a.call(f'_global.{STDINC}.{STDINC_INIT}', lambda s: s.get('_global'))
dbg(a, 'boot: globals')

# loadLevel(cb) : charge _root.lvl (XML) puis appelle cb(xml)
f = Asm()
dbg(f, 'loadLevel')
f.set('x', lambda s: s.new('XML'))
f.set('x.ktcb', lambda s: s.get('cb'))
on = Asm(); on.call('this.ktcb', lambda s: s.get('this'))
f.set('x.onLoad', lambda s: s.func('', ['ok'], on))
f.call('x.load', lambda s: s.get('_root.lvl'))
f.new('LoadVars').Return()
a.set(f'_global.{o("loadLevel")}', lambda s: s.func('', ['cb'], f))

# startGame() : prévient la page
f = Asm(); f.call(f'{EI}.call', 'ktPiouStart')
a.set(f'_global.{o("startGame")}', lambda s: s.func('', [], f))

# exitGame(data) : renvoie un LoadVars ; une image plus tard, si le jeu a branché onData
# (bouton REJOUER), on relance le niveau, sinon on transmet le résultat à la page.
f = Asm()
dbg(f, 'exitGame')
f.set('lv', lambda s: s.new('LoadVars'))
f.set('lv.ktd', lambda s: s.get('d'))
t = Asm()
dbg(t, 'exitGame: timer')
L = t.newlabel()
# LoadVars.prototype.onData existe toujours : seul un onData posé par le jeu (REJOUER) compte
t.get('lv.onData'); t.get('LoadVars.prototype.onData'); t.StrictEquals(); t.if_(L)
t.call(f'{EI}.call', 'ktPiouRetry')
t.call('lv.onData', None)
t.push(None).Return()
t.label(L)
t.call(f'{EI}.call', 'ktPiouExit', lambda s: s.get('d.$time'), lambda s: s.get('d.$piouz'), lambda s: s.get('d.$pid'))
f.call('_global.setTimeout', lambda s: s.func('', [], t), 60)
f.get('lv').Return()
a.set(f'_global.{o("exitGame")}', lambda s: s.func('', ['d'], f))

# saveLevel : inutilisé (éditeur)
f = Asm(); f.new('LoadVars').Return()
a.set(f'_global.{o("saveLevel")}', lambda s: s.func('', ['s', 'cb'], f))

# Manager.init(_root) puis Manager.main() à chaque image
dbg(a, 'boot: Manager.init')
if DEBUG:
    a.get(o('Manager')).TypeOf().Trace()
    a.get(o('Manager') + '.' + o('init')).TypeOf().Trace()
a.call(f'{o("Manager")}.{o("init")}', lambda s: s.get('this'))
dbg(a, 'boot: ok')
if DEBUG:
    for path in [f'_global.3Wt.{o("getGlobal")}', f'{o("Cs")}.{o("game")}', f'{o("Manager")}.{o("mode")}', f'{o("Game")}', f'{o("LoaderInterface")}.{o("loadLevel")}', f'_global.{o("loadLevel")}', f'{o("Game")}.{o("STAND_ALONE")}', f'{o("Cs")}.{o("game")}.{o("step")}', f'{o("Cs")}.{o("game")}.{o("gameMode")}', f'{o("Cs")}.{o("Lang")}', f'{o("Cs")}.{o("game")}.{o("mdm")}', f'{o("Cs")}.{o("game")}.{o("flPause")}', f'{o("Cs")}.{o("game")}.{o("hintList")}', f'{o("Cs")}.{o("game")}.{o("endTime")}', f'{o("Cs")}.{o("game")}.{o("slv")}']:
        a.push(path + ' = ').get(path).TypeOf().StringAdd().push(' ').StringAdd().get(path).StringAdd().Trace()
m = Asm(); m.call(f'{o("Manager")}.{o("main")}')
a.set('this.onEnterFrame', lambda s: s.func('', [], m))
a.Stop()

# ---------------------------------------------------------------- assemblage du SWF
tmp = avm1.read_swf(f'{SRC}/game/swf/temple.swf')
def encode_pool(pool):
    import struct
    payload = struct.pack('<H', len(pool)) + b''.join(x.encode('latin-1') + b'\0' for x in pool)
    return bytes([0x88]) + struct.pack('<H', len(payload)) + payload
tags = []
for c, d in tmp['tags']:
    if c == 12:
        assert d[0] == 0x88
        old_len = 3 + int.from_bytes(d[1:3], 'little')
        d = encode_pool(fixed_pool) + d[old_len:]
        tags.append((12, stdinc))
        tags.append((c, d))
        tags.append(avm1.do_action(a))
    else:
        tags.append((c, d))
tmp['tags'] = tags
tmp['rect'] = avm1.rect_bytes(622, 424)
avm1.write_swf(os.path.join(OUT, 'pioupiouz.swf'), tmp)

# ---------------------------------------------------------------- niveaux
sql = open(f'{SRC}/levels/levels.sql', encoding='utf-8').read()
body = sql[sql.index('VALUES', sql.index('INSERT INTO')) + 6:]
def parse(i):
    if body[i] == "'":
        j = i + 1; out = ''
        while True:
            c = body[j]
            if c == '\\': out += body[j+1]; j += 2; continue
            if c == "'": return out, j + 1
            out += c; j += 1
    if body.startswith('_binary ', i): return parse(i + 8)
    j = i
    while body[j] not in ',)': j += 1
    v = body[i:j]; return (None if v == 'NULL' else v), j
rows = []; i = 0
while i < len(body) and body[i] != ';':
    if body[i] == '(':
        i += 1; row = []
        while True:
            v, i = parse(i); row.append(v)
            if body[i] == ',': i += 1; continue
            i += 1; break
        rows.append(row)
    else: i += 1
cols = ('id userId title comment cdate official time piouz data touched selections plays success failures '
        'difficulty perfect visualNote interestNote votes soluce theme tutorial pos periodPlays').split()

def fix(t):
    # le dump contient du texte encodé plusieurs fois (UTF-8 relu en cp1252)
    if not t: return ''
    for _ in range(3):
        try: t = t.encode('cp1252').decode('utf-8')
        except UnicodeError: break
    return t

TUTO = {  # textes d'aide des tutoriels (les originaux ne sont pas dans l'archive)
 'creuseur': "Le Creuseur fait creuser le piou vers le bas. Cliquez sur l'action à droite, puis sur un piou.",
 'sauteur': "Le Sauteur fait bondir le piou ciblé par-dessus les obstacles.",
 'arc-en-ciel': "L'Arc-en-ciel crée un pont devant le piou : idéal pour franchir un ravin.",
 'vrilleur': "Le Vrilleur creuse droit devant lui à travers la roche.",
 'fleur': "La Fleur pousse sous le piou et le soulève vers les hauteurs.",
 'dérouleur': "Le Dérouleur se déroule pour former un pont que les autres piouz peuvent emprunter.",
 'pause': "Appuyez sur Espace (ou le bouton pause) pour figer le temps et préparer vos actions.",
 'crystal': "Le Crystal fait jaillir un cristal du sol, sous le piou ciblé.",
 'temps': "Le sablier accélère le temps : pratique quand les piouz marchent déjà dans la bonne direction.",
 'grenade': "Le Grenadier pose une grenade qui creuse un cratère en explosant.",
}
levels = []
for r in rows:
    d = dict(zip(cols, r))
    tuto = d['tutorial'] == '1'
    if not tuto and d['official'] != '1': continue
    title = fix(d['title'])
    key = title.replace('tuto ', '') if tuto else None
    lv = {'id': int(d['id']), 'title': title[0].upper() + title[1:], 'piouz': int(d['piouz']),
          'pos': int(d['pos']), 'theme': int(d['theme']), 'tuto': tuto,
          'difficulty': int(d['difficulty'] or 0), 'comment': fix(d['comment'])}
    help_ = TUTO.get(key, '') if tuto else ''
    x = (f'<r/><level status="0" piouz="{lv["piouz"]}" id="{lv["id"]}"><data>{d["data"]}</data>'
         + (f'<tuto>{help_}</tuto>' if help_ else '') + '</level>')
    open(os.path.join(OUT, 'levels', f'{lv["id"]}.xml'), 'w', encoding='utf-8').write(x)
    levels.append(lv)
TORDER = ['creuseur', 'sauteur', 'arc-en-ciel', 'fleur', 'vrilleur', 'crystal', 'dérouleur', 'grenade', 'pause', 'temps']
levels.sort(key=lambda l: (0, TORDER.index(l['title'].lower().replace('tuto ', ''))) if l['tuto'] else (1, l['pos']))
json.dump(levels, open(os.path.join(OUT, 'levels.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(levels), 'niveaux ;', os.path.getsize(os.path.join(OUT, 'pioupiouz.swf')), 'octets')
