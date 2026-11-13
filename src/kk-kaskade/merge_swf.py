#!/usr/bin/env python3
"""Reconstruit kaskade.swf comme le faisait swfmake.xml de Motion Twin :
base = swf/code.swf (symbole exporté "code"), include swf/gfx.swf link="*".
Usage : merge_swf.py code.swf gfx.swf sortie.swf
Le code n'est pas obfusqué (le loader KotionTwin expose aussi les noms clairs).
"""
import sys, zlib, struct

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

def main(code_swf, gfx_swf, out):
    ghdr, gbody, gpos = body_of(gfx_swf)
    _, cbody, cpos = body_of(code_swf)
    parts, maxid = [], 0
    for code, d in tags(gbody, gpos):
        if code in (0, 1, 4, 5, 26, 28, 70, 12, 69):
            continue  # timeline de travail du gfx et en-têtes : non repris
        if code in DEF_TAGS:
            maxid = max(maxid, struct.unpack('<H', d[:2])[0])
        parts.append(tag(code, d))
    newid = maxid + 1
    remap = {}
    for code, d in tags(cbody, cpos):
        if code == 39:
            old = struct.unpack('<H', d[:2])[0]
            remap[old] = newid
            parts.append(tag(39, struct.pack('<H', newid) + d[2:]))
        elif code == 56:
            n = struct.unpack('<H', d[:2])[0]
            i, ex = 2, b''
            for _ in range(n):
                cid = struct.unpack('<H', d[i:i + 2])[0]
                j = d.index(0, i + 2)
                ex += struct.pack('<H', remap.get(cid, cid)) + d[i + 2:j + 1]
                i = j + 1
            parts.append(tag(56, struct.pack('<H', n) + ex))
    parts.append(tag(1, b''))
    parts.append(tag(0, b''))
    body = ghdr + b''.join(parts)
    data = zlib.compress(body, 9)
    open(out, 'wb').write(b'CWS' + bytes([8]) + struct.pack('<I', len(body) + 8) + data)

if __name__ == '__main__':
    main(*sys.argv[1:4])
