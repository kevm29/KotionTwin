#!/usr/bin/env python3
"""swfmerge : fusionne des bibliothèques SWF (AVM1) dans un SWF de base, comme l'outil interne
« swfmake » de Motion Twin (<base file=...> + <include file=... link="*">).

Usage : swfmerge.py base.swf sortie.swf lib1.swf [lib2.swf ...]

Les définitions de chaque bibliothèque (formes, images, sons, polices, sprites, boutons, textes),
ses ExportAssets et ses DoInitAction sont renumérotés puis insérés avant la première image du
SWF de base. Les identifiants référencés à l'intérieur des tags (remplissages bitmap des formes,
polices des textes, contenus des sprites et boutons…) sont réécrits.
"""
import struct, sys, zlib

class Bits:
    def __init__(self, b, pos): self.b = b; self.byte = pos; self.bit = 0
    def ub(self, n):
        v = 0
        for _ in range(n):
            v = (v << 1) | ((self.b[self.byte] >> (7 - self.bit)) & 1)
            self.bit += 1
            if self.bit == 8: self.bit = 0; self.byte += 1
        return v
    def sb(self, n):
        v = self.ub(n)
        return v - (1 << n) if n and v >> (n - 1) else v
    def align(self):
        if self.bit: self.bit = 0; self.byte += 1
        return self.byte

def rect_end(b, p):
    bt = Bits(b, p); n = bt.ub(5); bt.ub(4 * n); return bt.align()

def matrix_end(b, p):
    bt = Bits(b, p)
    if bt.ub(1): n = bt.ub(5); bt.ub(2 * n)
    if bt.ub(1): n = bt.ub(5); bt.ub(2 * n)
    n = bt.ub(5); bt.ub(2 * n); return bt.align()

def cxform_end(b, p, alpha):
    bt = Bits(b, p); ha = bt.ub(1); hm = bt.ub(1); n = bt.ub(4); k = 4 if alpha else 3
    if ha: bt.ub(n * k)
    if hm: bt.ub(n * k)
    return bt.align()

def gradient_end(b, p, shape_ver, focal=False):
    n = b[p] & 15; p += 1
    p += n * (1 + (4 if shape_ver >= 3 else 3))
    if focal: p += 2
    return p

class Merger:
    def __init__(self, idmap): self.m = idmap
    def fix(self, b, p):
        old = struct.unpack_from('<H', b, p)[0]
        if old in self.m: struct.pack_into('<H', b, p, self.m[old])

    # -- styles de remplissage : réécrit les identifiants de bitmap
    def fillstyles(self, b, p, ver):
        n = b[p]; p += 1
        if n == 0xFF and ver >= 2: n = struct.unpack_from('<H', b, p)[0]; p += 2
        for _ in range(n):
            t = b[p]; p += 1
            if t == 0x00: p += 4 if ver >= 3 else 3
            elif t in (0x10, 0x12, 0x13): p = matrix_end(b, p); p = gradient_end(b, p, ver, t == 0x13)
            elif t in (0x40, 0x41, 0x42, 0x43): self.fix(b, p); p += 2; p = matrix_end(b, p)
            else: raise ValueError(f'fill style {t:#x}')
        return p
    def linestyles(self, b, p, ver):
        n = b[p]; p += 1
        if n == 0xFF: n = struct.unpack_from('<H', b, p)[0]; p += 2
        for _ in range(n):
            if ver == 4:
                p += 2; f1 = b[p]; f2 = b[p + 1]; p += 2
                if ((f1 >> 4) & 3) == 2: p += 2  # join miter
                if f1 & 0x08: p = self.fillstyles_one(b, p, ver)
                else: p += 4
            else: p += 2 + (4 if ver >= 3 else 3)
        return p
    def fillstyles_one(self, b, p, ver):
        t = b[p]; p += 1
        if t == 0x00: return p + 4
        if t in (0x10, 0x12, 0x13): p = matrix_end(b, p); return gradient_end(b, p, ver, t == 0x13)
        self.fix(b, p); p += 2; return matrix_end(b, p)
    def shape_records(self, b, p, ver):
        bt = Bits(b, p); nf = bt.ub(4); nl = bt.ub(4)
        while True:
            if bt.ub(1):  # edge
                straight = bt.ub(1); n = bt.ub(4) + 2
                if straight:
                    if bt.ub(1): bt.ub(2 * n)
                    else: bt.ub(1); bt.ub(n)
                else: bt.ub(4 * n)
            else:
                flags = bt.ub(5)
                if flags == 0: return
                if flags & 1: n = bt.ub(5); bt.ub(2 * n)
                if flags & 2: bt.ub(nf)
                if flags & 4: bt.ub(nf)
                if flags & 8: bt.ub(nl)
                if flags & 16:
                    q = bt.align(); q = self.fillstyles(b, q, ver); q = self.linestyles(b, q, ver)
                    bt = Bits(b, q); nf = bt.ub(4); nl = bt.ub(4)
    def shape(self, b, ver):
        p = rect_end(b, 2)
        if ver == 4: p = rect_end(b, p); p += 1
        p = self.fillstyles(b, p, ver); p = self.linestyles(b, p, ver)
        self.shape_records(b, p, ver)
    def morph(self, b, ver):
        p = rect_end(b, 2); p = rect_end(b, p)
        if ver == 2: p = rect_end(b, p); p = rect_end(b, p); p += 1
        p += 4  # offset
        n = b[p]; p += 1
        if n == 0xFF: n = struct.unpack_from('<H', b, p)[0]; p += 2
        for _ in range(n):
            t = b[p]; p += 1
            if t == 0: p += 8
            elif t in (0x10, 0x12, 0x13):
                p = matrix_end(b, p); p = matrix_end(b, p); k = b[p]; p += 1 + k * 10
            else: self.fix(b, p); p += 2; p = matrix_end(b, p); p = matrix_end(b, p)
    def text(self, b, ver):
        p = rect_end(b, 2); p = matrix_end(b, p)
        gb = b[p]; ab = b[p + 1]; p += 2
        while True:
            f = b[p]; p += 1
            if f == 0: return
            if f & 8: self.fix(b, p); p += 2
            if f & 4: p += 4 if ver == 2 else 3
            if f & 1: p += 2
            if f & 2: p += 2
            if f & 8: p += 2
            n = b[p]; p += 1
            bt = Bits(b, p); bt.ub(n * (gb + ab)); p = bt.align()
    def edittext(self, b):
        p = rect_end(b, 2); f = struct.unpack_from('>H', b, p)[0]; p += 2
        if f & 0x0100: self.fix(b, p)  # HasFont
    def place2(self, b, p0, v3=False):
        flags = b[p0]; p = p0 + 1
        if v3: f2 = b[p]; p += 1
        p += 2  # depth
        if v3 and ((f2 & 0x08) or ((f2 & 0x10) and (flags & 0x02))):
            # class name
            p = b.index(b'\0', p) + 1
        if flags & 0x02: self.fix(b, p)
    def button_records(self, b, p, v2):
        while b[p] != 0:
            flags = b[p]; self.fix(b, p + 1); p += 5
            p = matrix_end(b, p)
            if v2: p = cxform_end(b, p, True)
            if v2 and flags & 0x10: raise ValueError('filtres de bouton non gérés')
            if v2 and flags & 0x20: p += 1
        return p

    def rewrite(self, code, t):
        """Renvoie le tag (bytes) avec ses identifiants réécrits."""
        b = bytearray(t); m = self
        DEF_ID = {2, 22, 32, 83, 6, 21, 35, 20, 36, 90, 7, 34, 10, 48, 75, 11, 33, 37, 14, 39, 46, 84, 60}
        REF_ID = {13, 62, 73, 88, 23, 17, 78, 74, 61, 59, 5}  # premier UI16 = référence
        if code in DEF_ID or code in REF_ID: self.fix(b, 0)
        if code in (2, 22): self.shape(b, 1 if code == 2 else 2)
        elif code == 32: self.shape(b, 3)
        elif code == 83: self.shape(b, 4)
        elif code == 46: self.morph(b, 1)
        elif code == 84: self.morph(b, 2)
        elif code in (11, 33): self.text(b, 1 if code == 11 else 2)
        elif code == 37: self.edittext(b)
        elif code == 4: self.fix(b, 0)
        elif code == 26: self.place2(b, 0)
        elif code == 70: self.place2(b, 0, True)
        elif code == 15: self.fix(b, 0)  # StartSound
        elif code == 7: self.button_records(b, 2, False)
        elif code == 34: self.button_records(b, 5, True)
        elif code == 17:
            p = 2
            for _ in range(4):
                sid = struct.unpack_from('<H', b, p)[0]; self.fix(b, p); p += 2
                if sid:
                    fl = b[p]; p += 1
                    if fl & 1: p += 4
                    if fl & 2: p += 4
                    if fl & 4: p += 2
                    if fl & 8: n = b[p]; p += 1 + 8 * n
        elif code == 56:
            n = struct.unpack_from('<H', b, 0)[0]; p = 2
            for _ in range(n): self.fix(b, p); p = b.index(b'\0', p + 2) + 1
        elif code == 39:
            out = bytearray(b[:4]); p = 4
            for c2, t2 in tags(bytes(b), 4):
                out += mktag(c2, self.rewrite(c2, t2))
            return bytes(out)
        return bytes(b)

def tags(b, p):
    while p < len(b):
        h = struct.unpack_from('<H', b, p)[0]; p += 2; code, ln = h >> 6, h & 63
        if ln == 63: ln = struct.unpack_from('<I', b, p)[0]; p += 4
        yield code, b[p:p + ln]; p += ln
        if code == 0: return

LONG_TAGS = {6, 21, 35, 20, 36, 90, 14, 19, 39}
def mktag(code, data):
    if len(data) < 63 and code not in LONG_TAGS: return struct.pack('<H', (code << 6) | len(data)) + data
    return struct.pack('<HI', (code << 6) | 63, len(data)) + data

def load(path):
    raw = open(path, 'rb').read()
    b = raw[:8] + (zlib.decompress(raw[8:]) if raw[:3] == b'CWS' else raw[8:])
    hdr_end = rect_end(b, 8) + 4
    return raw[3], b, hdr_end

DEFINES = {2, 22, 32, 83, 6, 21, 35, 20, 36, 90, 7, 34, 10, 48, 75, 11, 33, 37, 14, 39, 46, 84, 60}

def main():
    args = sys.argv[1:]; size = None
    if '--size' in args:
        i = args.index('--size'); size = [float(x) for x in args[i + 1].split('x')]; del args[i:i + 2]
    hide = []  # --hide NOM : retire un nom d'export (ex. boutons de triche laissés dans un build de debug)
    while '--hide' in args:
        i = args.index('--hide'); hide.append(args[i + 1].encode()); del args[i:i + 2]
    base, out, libs = args[0], args[1], args[2:]
    ver, b, he = load(base)
    btags = list(tags(b, he))
    used = set()
    def strip(t):
        n = struct.unpack_from('<H', t)[0]; p = 2; keep = []
        for _ in range(n):
            e = t.index(b'\0', p + 2)
            if t[p + 2:e] not in hide: keep.append(t[p:e + 1])
            p = e + 1
        return struct.pack('<H', len(keep)) + b''.join(keep)
    if hide: btags = [(c, strip(t) if c == 56 else t) for c, t in btags]
    for c, t in btags:
        if c in DEFINES: used.add(struct.unpack_from('<H', t, 0)[0])
    nxt = max(used) + 1 if used else 1
    exported = set()
    for c, t in btags:
        if c == 56:
            n = struct.unpack_from('<H', t)[0]; p = 2
            for _ in range(n):
                e = t.index(b'\0', p + 2); exported.add(t[p + 2:e]); p = e + 1
    inserted = []
    for lib in libs:
        _, lb, lhe = load(lib)
        idmap = {}
        ltags = list(tags(lb, lhe))
        for c, t in ltags:
            if c in DEFINES:
                old = struct.unpack_from('<H', t, 0)[0]; idmap[old] = nxt; nxt += 1
        m = Merger(idmap)
        # DefineBits + JPEGTables -> DefineBitsJPEG2 (les tables sont propres à chaque bibliothèque)
        jt = b''.join(t for c, t in ltags if c == 8)
        for c, t in [((21, t[:2] + jt + t[2:]) if c == 6 else (c, t)) for c, t in ltags if c != 8]:
            if c in (0, 1, 9, 69, 77, 24, 64, 65, 43, 12, 26, 70, 4, 5, 28, 15, 18, 19, 45):
                continue  # en-têtes et contenu de la scène principale de la bibliothèque : ignorés
            nt = m.rewrite(c, t)
            if c == 56:  # ne pas réexporter un nom déjà fourni par la base
                n = struct.unpack_from('<H', nt)[0]; p = 2; keep = []
                for _ in range(n):
                    e = nt.index(b'\0', p + 2); name = nt[p + 2:e]
                    if name not in exported and name not in hide: keep.append(nt[p:e + 1]); exported.add(name)
                    p = e + 1
                if not keep: continue
                nt = struct.pack('<H', len(keep)) + b''.join(keep)
            inserted.append(mktag(c, nt))
    # insertion avant la première image (après FileAttributes/SetBackgroundColor/Metadata)
    hdr = b[8:he]
    if size:  # nouvelle taille de scène (recadrage, comme la fenêtre Frusion d'origine)
        sys.path.insert(0, __import__('os').path.dirname(__file__))
        from as1c import rect_bytes
        hdr = rect_bytes(*size) + b[rect_end(b, 8):he]
    body = bytearray(hdr); done = False
    for c, t in btags:
        if not done and c not in (69, 9, 77, 24, 64, 65):
            body += b''.join(inserted); done = True
        body += mktag(c, t)
    data = bytes(body)
    res = b'CWS' + bytes([ver]) + struct.pack('<I', len(data) + 8) + zlib.compress(data, 9)
    open(out, 'wb').write(res)
    print(f'{out}: {len(inserted)} tags insérés, ids {min(used) if used else 0}..{nxt - 1}')

if __name__ == '__main__':
    main()
