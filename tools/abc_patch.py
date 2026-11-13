#!/usr/bin/env python3
"""Petit outil de retouche de bytecode AVM2 (ABC) dans un SWF, sans dépendance.

Permet d'ajouter des chaînes / multinames au pool de constantes et de remplacer
le corps d'une méthode. Utilisé par les restaurations Arkadeo (voir
platforms/arkadeo/README.md).
"""
import zlib, struct

def u30(v):
    out = bytearray()
    while True:
        b = v & 0x7f; v >>= 7
        if v: out.append(b | 0x80)
        else: out.append(b); return bytes(out)

class Reader:
    def __init__(s, d, p=0): s.d = d; s.p = p
    def u8(s): v = s.d[s.p]; s.p += 1; return v
    def u16(s): v = struct.unpack('<H', s.d[s.p:s.p+2])[0]; s.p += 2; return v
    def u30(s):
        r = 0; sh = 0
        for _ in range(5):
            b = s.u8(); r |= (b & 0x7f) << sh; sh += 7
            if not b & 0x80: break
        return r

class Abc:
    """Analyse minimale qui note les positions utiles."""
    def __init__(s, data):
        s.data = bytearray(data)
        r = Reader(s.data); r.p = 4
        for kind in ('int', 'uint'):
            n = r.u30()
            for _ in range(max(0, n - 1)): r.u30()
        n = r.u30(); r.p += 8 * max(0, n - 1)
        s.str_count_pos = r.p; n = r.u30(); s.strs = ['']
        for _ in range(n - 1):
            l = r.u30(); s.strs.append(bytes(s.data[r.p:r.p+l]).decode('utf8', 'replace')); r.p += l
        s.str_end = r.p
        n = r.u30(); s.ns = [(0, '')]
        for _ in range(n - 1): k = r.u8(); s.ns.append((k, s.strs[r.u30()]))
        n = r.u30()
        for _ in range(n - 1): [r.u30() for _ in range(r.u30())]
        s.mn_count_pos = r.p; n = r.u30(); s.mn = [None]
        for _ in range(n - 1):
            k = r.u8()
            if k in (7, 0xd): s.mn.append(('Q', r.u30(), r.u30()))
            elif k in (0xf, 0x10): s.mn.append(('RTQ', r.u30()))
            elif k in (0x11, 0x12): s.mn.append(('RTQL',))
            elif k in (9, 0xe): s.mn.append(('M', r.u30(), r.u30()))
            elif k in (0x1b, 0x1c): s.mn.append(('ML', r.u30()))
            elif k == 0x1d: t = r.u30(); s.mn.append(('G', t, [r.u30() for _ in range(r.u30())]))
        s.mn_end = r.p

    def find_string(s, v):
        return s.strs.index(v) if v in s.strs else None

    def find_ns(s, kind, name):
        for i, (k, n) in enumerate(s.ns):
            if i and k == kind and n == name: return i
        return None

    def find_qname(s, nsname, name):
        for i, m in enumerate(s.mn):
            if m and m[0] == 'Q' and s.strs[m[2]] == name and s.ns[m[1]] == (0x16, nsname): return i
        return None

    def add_string(s, v):
        i = s.find_string(v)
        if i is not None: return i
        b = v.encode('utf8'); ins = u30(len(b)) + b
        s.data[s.str_end:s.str_end] = ins
        old = Reader(s.data, s.str_count_pos); n = old.u30(); oldlen = old.p - s.str_count_pos
        new = u30(n + 1); s.data[s.str_count_pos:s.str_count_pos+oldlen] = new
        s.__init__(bytes(s.data)); return n

    def add_qname(s, nsname, name):
        i = s.find_qname(nsname, name)
        if i is not None: return i
        si = s.add_string(name)
        ni = s.find_ns(0x16, nsname)
        assert ni is not None, 'namespace absent : ' + nsname
        ins = bytes([7]) + u30(ni) + u30(si)
        s.data[s.mn_end:s.mn_end] = ins
        old = Reader(s.data, s.mn_count_pos); n = old.u30(); oldlen = old.p - s.mn_count_pos
        s.data[s.mn_count_pos:s.mn_count_pos+oldlen] = u30(n + 1)
        s.__init__(bytes(s.data)); return n

def swf_read(path):
    b = open(path, 'rb').read()
    body = zlib.decompress(b[8:]) if b[:3] == b'CWS' else b[8:]
    nbits = body[0] >> 3; rl = (5 + 4 * nbits + 7) // 8
    header = body[:rl+4]; pos = rl + 4; tags = []
    while pos + 2 <= len(body):
        th = struct.unpack('<H', body[pos:pos+2])[0]; code = th >> 6; ln = th & 63; pos += 2
        if ln == 63: ln = struct.unpack('<I', body[pos:pos+4])[0]; pos += 4
        tags.append([code, body[pos:pos+ln]]); pos += ln
        if code == 0: break
    return b[3], header, tags

def swf_write(path, ver, header, tags):
    out = bytearray(header)
    for c, d in tags:
        out += struct.pack('<HI', (c << 6) | 63, len(d)) + d
    open(path, 'wb').write(b'CWS' + bytes([ver]) + struct.pack('<I', len(out) + 8) + zlib.compress(bytes(out), 9))

def method_bodies(abcdata, abcdump_ABC):
    """Renvoie {indice_methode: (debut, fin)} des corps de méthode."""
    a = abcdump_ABC
    return a

def replace_body(data, method_index, code, max_stack, local_count, init_scope, max_scope):
    """Remplace le corps de la méthode method_index (data = ABC complet)."""
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    r = Reader(bytearray(data), 0)
    # on re-parcourt tout l'ABC jusqu'aux corps de méthodes avec abcdump-like
    from abc_positions import body_positions
    pos = body_positions(bytes(data))
    start, end = pos[method_index]
    rr = Reader(data, start); rr.u30()
    for _ in range(4): rr.u30()
    cl = rr.u30(); rr.p += cl
    ne = rr.u30(); assert ne == 0, 'exceptions non gérées'
    traits_start = rr.p
    nb = u30(method_index) + u30(max_stack) + u30(local_count) + u30(init_scope) + u30(max_scope) + u30(len(code)) + bytes(code) + u30(0)
    return bytes(data[:start]) + nb + bytes(data[traits_start:])
