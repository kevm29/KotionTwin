#!/usr/bin/env python3
"""Reconstruit games/dinocard/ à partir de l'archive WebGamesArchives.

    python3 -I src/dinocard/build.py <chemin>/WebGamesArchives/Dinocard

- client/swf/temple.swf : le lecteur de combat d'origine, utilisé tel quel (il lit $info,
  télécharge le combat sérialisé par mt.PersistCodec et le rejoue) ;
- client/swf/avatar.swf : la bibliothèque d'avatars chargée par le lecteur ;
- gfx/card/artwork/*.jpg : les illustrations des cartes ;
- cards.json : la base des cartes n'est pas dans l'archive (elle vivait côté serveur).
  On en fabrique une à partir des illustrations : élément déduit de la teinte dominante
  de l'image, nom et caractéristiques générés de façon déterministe à partir de l'id.
"""
import sys, os, json, shutil, colorsys, random
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
SRC = sys.argv[1] if len(sys.argv) > 1 else '../WebGamesArchives/Dinocard'
OUT = os.path.join(ROOT, 'games', 'dinocard')
os.makedirs(os.path.join(OUT, 'art'), exist_ok=True)

for f in ('temple.swf', 'avatar.swf'):
    shutil.copy(os.path.join(SRC, 'client', 'swf', f), os.path.join(OUT, f))

ART = os.path.join(SRC, 'gfx', 'card', 'artwork')
ids = sorted(int(f[:-4]) for f in os.listdir(ART) if f.endswith('.jpg'))

def element(path):
    im = Image.open(path).convert('RGB').resize((48, 36))
    hist = [0.0] * 5
    for r, g, b in im.getdata():
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        w = s * v
        if w < 0.15: hist[4] += 0.12; continue          # tons pâles : ciel
        d = h * 360
        if d < 35 or d >= 330: hist[0] += w             # rouge / orange : feu
        elif d < 70: hist[3] += w                       # jaune : foudre
        elif d < 165: hist[1] += w                      # vert : bois
        elif d < 255: hist[2] += w                      # bleu : eau
        else: hist[4] += w                              # violet / rose : ciel
    return max(range(5), key=lambda i: hist[i])

SYL = [['pyr', 'ign', 'braz', 'flam', 'kal', 'sol', 'roug', 'vulc'],
       ['syl', 'mous', 'fol', 'ronc', 'gland', 'arb', 'lich', 'tronc'],
       ['aqu', 'mar', 'hydr', 'goutt', 'flot', 'cora', 'perl', 'ond'],
       ['volt', 'zap', 'tonn', 'stat', 'ful', 'bzz', 'eclai', 'joul'],
       ['nub', 'aer', 'plum', 'vent', 'azur', 'brum', 'stra', 'zeph']]
MID = ['a', 'o', 'i', 'u', 'e', 'ou', 'y']
END = ['dor', 'rex', 'zor', 'mos', 'nax', 'pik', 'tis', 'gon', 'lux', 'mak', 'ron', 'bul', 'kid', 'nok']
cards, used = [], set()
for cid in ids:
    rnd = random.Random(cid * 7919)
    el = element(os.path.join(ART, f'{cid}.jpg'))
    while True:
        name = (rnd.choice(SYL[el]) + rnd.choice(MID) + rnd.choice(END)).capitalize()
        if name not in used: used.add(name); break
    ecl = rnd.choice([1, 1, 2, 2, 2, 3, 3, 4])
    budget = 3 + ecl * 2 + rnd.randint(-1, 1)
    st = max(1, min(budget - 1, rnd.randint(1, budget - 1)))
    en = max(1, budget - st)
    cards.append({'id': cid, 'element': el, 'name': name, 'eclosion': ecl,
                  'strength': st, 'endurance': en, 'energy': 'FBEJC'[el] * (1 + (ecl >= 3))})
    shutil.copy(os.path.join(ART, f'{cid}.jpg'), os.path.join(OUT, 'art', f'{cid}.jpg'))
json.dump(cards, open(os.path.join(OUT, 'cards.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(cards), 'cartes ; par élément :', [sum(c['element'] == e for c in cards) for e in range(5)])
