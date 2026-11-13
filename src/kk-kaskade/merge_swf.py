#!/usr/bin/env python3
"""Reconstruit kaskade.swf comme le faisait swfmake.xml de Motion Twin :
base = swf/code.swf (symbole exporté "code"), include swf/gfx.swf link="*".
Usage : merge_swf.py code.swf gfx.swf sortie.swf [obfmap.json]
Avec obfmap.json, les noms du pool de constantes et les noms d'export sont renommés
comme le faisait l'obfuscateur Motion Twin (hachage déterministe commun à tous les
jeux), ce qui permet d'utiliser la bibliothèque d'exécution MotionTypes d'origine.
"""
import sys, zlib, struct, json

def obf_actions(d, m):
    """Renomme les entrées du ConstantPool (0x88) au début d'un bloc d'actions."""
    out, pos = b'', 0
    while pos < len(d):
        op = d[pos]
        if op == 0:
            out += d[pos:]; break
        ln = struct.unpack('<H', d[pos + 1:pos + 3])[0] if op >= 0x80 else 0
        hl = 3 if op >= 0x80 else 1
        chunk = d[pos:pos + hl + ln]
        if op == 0x88:
            n = struct.unpack('<H', chunk[3:5])[0]; i = 5; names = []
            for _ in range(n):
                j = chunk.index(0, i); names.append(chunk[i:j].decode('latin1')); i = j + 1
            data = struct.pack('<H', n) + b''.join(m.get(x, x).encode('latin1') + b'\0' for x in names)
            chunk = bytes([0x88]) + struct.pack('<H', len(data)) + data
            out += chunk + d[pos + hl + ln:]
            return out
        out += chunk; pos += hl + ln
    return out

DEF_TAGS = {2,6,10,11,13,14,20,21,22,32,33,34,35,36,37,39,46,48,60,62,73,75,83,84,87,88,90,91}

def body_of(path):
    b = open(path, 'rb').read()
    body = zlib.decompress(b[8:]) if b[:3] == b'CWS' else b[8:]
    nb = body[0] >> 3
    rl = (5 + 4 * nb + 7) // 8
    return body[:rl + 4], body, rl + 4

def tags(body, pos):
    while pos < len(body):
        th = struct.unpack('<H', body[pos:pos + 2])[0]
        code, ln, start = th >> 6, th & 63, pos
        pos += 2
        if ln == 63:
            ln = struct.unpack('<I', body[pos:pos + 4])[0]
            pos += 4
        yield code, body[pos:pos + ln]
        pos += ln
        if code == 0:
            break

def tag(code, data):
    if len(data) < 63 and code not in (20, 21, 35, 36, 6, 39):
        return struct.pack('<H', (code << 6) | len(data)) + data
    return struct.pack('<HI', (code << 6) | 63, len(data)) + data

def main(code_swf, gfx_swf, out, mapfile=None):
    m = json.load(open(mapfile)) if mapfile else {}
    ghdr, gbody, gpos = body_of(gfx_swf)
    _, cbody, cpos = body_of(code_swf)
    parts, maxid = [], 0
    for code, d in tags(gbody, gpos):
        if code in (0, 1, 4, 5, 26, 28, 70, 12, 69):
            continue  # timeline de travail du gfx et en-têtes : non repris
        if code == 56 and m:
            n = struct.unpack('<H', d[:2])[0]; i, ex = 2, b''
            for _ in range(n):
                j = d.index(0, i + 2)
                name = d[i + 2:j].decode('latin1')
                ex += d[i:i + 2] + m.get(name, name).encode('latin1') + b'\0'; i = j + 1
            d = struct.pack('<H', n) + ex
        if code in DEF_TAGS:
            maxid = max(maxid, struct.unpack('<H', d[:2])[0])
        parts.append(tag(code, d))
    newid = maxid + 1
    remap = {}
    for code, d in tags(cbody, cpos):
        if code == 39:
            old = struct.unpack('<H', d[:2])[0]
            remap[old] = newid
            inner = d[4:]
            if m:  # le sprite de code contient un seul DoAction suivi de ShowFrame/End
                th = struct.unpack('<H', inner[:2])[0]; ln = th & 63; hp = 2
                if ln == 63: ln = struct.unpack('<I', inner[2:6])[0]; hp = 6
                if th >> 6 == 12:
                    inner = tag(12, obf_actions(inner[hp:hp + ln], m)) + inner[hp + ln:]
            parts.append(tag(39, struct.pack('<H', newid) + d[2:4] + inner))
        elif code == 56:
            n = struct.unpack('<H', d[:2])[0]
            i, ex = 2, b''
            for _ in range(n):
                cid = struct.unpack('<H', d[i:i + 2])[0]
                j = d.index(0, i + 2)
                name = d[i + 2:j].decode('latin1')
                ex += struct.pack('<H', remap.get(cid, cid)) + m.get(name, name).encode('latin1') + b'\0'
                i = j + 1
            parts.append(tag(56, struct.pack('<H', n) + ex))
    parts.append(tag(1, b''))
    parts.append(tag(0, b''))
    body = ghdr + b''.join(parts)
    data = zlib.compress(body, 9)
    open(out, 'wb').write(b'CWS' + bytes([8]) + struct.pack('<I', len(body) + 8) + data)

if __name__ == '__main__':
    main(*sys.argv[1:5])
