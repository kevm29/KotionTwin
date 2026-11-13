#!/usr/bin/env python3
"""Affiche version, taille de scène (px), fps et nombre d'images d'un SWF."""
import sys, zlib, struct
for p in sys.argv[1:]:
    raw = open(p, 'rb').read()
    b = raw[:8] + (zlib.decompress(raw[8:]) if raw[:3] == b'CWS' else raw[8:])
    nb = b[8] >> 3; bits = int.from_bytes(b[8:8+(5+4*nb+7)//8], 'big'); tot = ((5+4*nb+7)//8)*8
    vals = [(bits >> (tot-5-nb*(i+1))) & ((1 << nb)-1) for i in range(4)]
    vals = [v - (1 << nb) if v >> (nb-1) else v for v in vals]
    off = 8 + (5+4*nb+7)//8
    fps = b[off+1] + b[off]/256; frames = struct.unpack_from('<H', b, off+2)[0]
    print(f'{p}: v{raw[3]} {(vals[1]-vals[0])/20:g}x{(vals[3]-vals[2])/20:g} {fps:g}fps {frames}f {len(raw)}o')
