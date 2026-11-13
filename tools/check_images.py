#!/usr/bin/env python3
"""Vérifie les images bitmap d'un ou plusieurs SWF (DefineBits*, DefineBitsLossless*) :
chacune doit se décoder et ne pas être vide (entièrement transparente ou d'une seule couleur).

Usage : python3 -I tools/check_images.py a.swf [b.swf …]
"""
import sys, os, io, zlib, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import avm1
from PIL import Image

def jpeg(data):
    data = data.replace(b'\xff\xd9\xff\xd8', b'')
    im = Image.open(io.BytesIO(data)); im.load(); return im

def check(path):
    swf = avm1.read_swf(path); tables = b''; res = {'ok': 0, 'vides': [], 'erreurs': []}
    for code, d in swf['tags']:
        try:
            if code == 8: tables = d
            elif code in (6, 21, 35):
                cid = struct.unpack('<H', d[:2])[0]
                if code == 6: im = jpeg(tables + d[2:])
                elif code == 21: im = jpeg(d[2:])
                else:
                    n = struct.unpack('<I', d[2:6])[0]; im = jpeg(d[6:6 + n])
                    alpha = zlib.decompress(d[6 + n:]) if len(d) > 6 + n else None
                    if alpha is not None and not any(alpha): res['vides'].append(cid); continue
                ex = im.convert('RGB').getextrema()
                if all(a == b for a, b in ex) and im.width * im.height > 4: res['vides'].append(cid); continue
                res['ok'] += 1
            elif code in (20, 36):
                cid, fmt, w, h = struct.unpack('<HBHH', d[:7])
                raw = zlib.decompress(d[7 + (fmt == 3):])
                if code == 36 and fmt == 5 and not any(raw[i] for i in range(0, len(raw), 4)):
                    res['vides'].append(cid); continue
                if len(set(raw[i:i + 4] for i in range(0, min(len(raw), 400000), 4))) <= 1 and w * h > 4:
                    res['vides'].append(cid); continue
                res['ok'] += 1
        except Exception as e:
            res['erreurs'].append((code, str(e)[:60]))
    return res

for p in sys.argv[1:]:
    r = check(p)
    print(f"{os.path.basename(p)} : {r['ok']} images valides, vides : {r['vides'] or 'aucune'}, erreurs : {r['erreurs'] or 'aucune'}")
