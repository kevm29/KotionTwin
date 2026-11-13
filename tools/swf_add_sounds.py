#!/usr/bin/env python3
"""Ajoute des sons (DefineSound + SymbolClass) dans un SWF AS3.

Usage : swf_add_sounds.py entree.swf sortie.swf Classe1=fichier1.wav Classe2=fichier2.mp3 ...

Chaque fichier est converti en MP3 44,1 kHz mono par ffmpeg, puis inséré comme
DefineSound et lié à la classe AS3 indiquée (qui doit déjà exister dans le SWF et
hériter de flash.media.Sound). Sert à rendre leurs sons aux jeux compilés avec
« -D disableSfx » (classes _SFX_* vides), par exemple Green Witch (Arkadeo).
"""
import sys, zlib, struct, subprocess, tempfile, os

def read_swf(path):
    b = open(path, 'rb').read()
    sig, ver = b[:3], b[3]
    body = zlib.decompress(b[8:]) if sig == b'CWS' else b[8:]
    nbits = body[0] >> 3
    rl = (5 + 4 * nbits + 7) // 8
    header = body[:rl + 4]
    pos = rl + 4
    tags = []
    while pos + 2 <= len(body):
        th = struct.unpack('<H', body[pos:pos + 2])[0]; code = th >> 6; ln = th & 63; pos += 2
        if ln == 63: ln = struct.unpack('<I', body[pos:pos + 4])[0]; pos += 4
        tags.append([code, body[pos:pos + ln]]); pos += ln
        if code == 0: break
    return ver, header, tags

def tag_bytes(code, data):
    if len(data) < 63 and code not in (14, 20, 21, 35, 36, 6, 87):
        return struct.pack('<H', (code << 6) | len(data)) + data
    return struct.pack('<HI', (code << 6) | 63, len(data)) + data

def write_swf(path, ver, header, tags):
    body = header + b''.join(tag_bytes(c, d) for c, d in tags)
    out = b'CWS' + bytes([ver]) + struct.pack('<I', len(body) + 8) + zlib.compress(body, 9)
    open(path, 'wb').write(out)

BITRATES = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]
def mp3_frames(data):
    """Renvoie (frames, nb_echantillons) pour un flux MPEG-1 Layer III."""
    i = 0; frames = bytearray(); n = 0
    if data[:3] == b'ID3':
        sz = (data[6] << 21) | (data[7] << 14) | (data[8] << 7) | data[9]
        i = 10 + sz
    while i + 4 <= len(data):
        if data[i] != 0xFF or (data[i + 1] & 0xE0) != 0xE0:
            i += 1; continue
        ver = (data[i + 1] >> 3) & 3; layer = (data[i + 1] >> 1) & 3
        bri = data[i + 2] >> 4; sri = (data[i + 2] >> 2) & 3; pad = (data[i + 2] >> 1) & 1
        if ver != 3 or layer != 1 or bri in (0, 15) or sri == 3:
            i += 1; continue
        sr = [44100, 48000, 32000][sri]
        size = 144000 * BITRATES[bri] // sr + pad
        frames += data[i:i + size]; n += 1152; i += size
    return bytes(frames), n

def to_mp3(src):
    fd, tmp = tempfile.mkstemp(suffix='.mp3'); os.close(fd)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ac', '1', '-ar', '44100', '-b:a', '96k',
                    '-write_xing', '0', '-id3v2_version', '0', '-f', 'mp3', tmp], check=True)
    d = open(tmp, 'rb').read(); os.unlink(tmp)
    return d

def main():
    src, dst = sys.argv[1], sys.argv[2]
    pairs = [a.split('=', 1) for a in sys.argv[3:]]
    ver, header, tags = read_swf(src)
    used = set()
    for c, d in tags:
        if c in (2, 22, 32, 83, 6, 20, 21, 35, 36, 90, 10, 48, 75, 91, 14, 39, 87, 7, 34, 37, 11, 33, 46, 84, 60, 13, 88):
            if len(d) >= 2: used.add(struct.unpack('<H', d[:2])[0])
    nid = max(used | {0}) + 1
    new_tags = []; syms = []
    for cls, f in pairs:
        frames, samples = mp3_frames(to_mp3(f))
        flags = (2 << 4) | (3 << 2) | (1 << 1) | 0  # MP3, 44 kHz, 16 bits, mono
        data = struct.pack('<HBI', nid, flags, samples) + struct.pack('<h', 0) + frames
        new_tags.append([14, data]); syms.append((nid, cls)); nid += 1
    sym = struct.pack('<H', len(syms)) + b''.join(struct.pack('<H', i) + n.encode() + b'\0' for i, n in syms)
    # DefineSound avant le premier ShowFrame, SymbolClass juste après le dernier DoABC de la 1re image
    first_show = next(i for i, t in enumerate(tags) if t[0] == 1)
    last_abc = max(i for i, t in enumerate(tags[:first_show]) if t[0] in (72, 82))
    tags = tags[:last_abc + 1] + new_tags + [[76, sym]] + tags[last_abc + 1:]
    write_swf(dst, ver, header, tags)
    print('%d sons ajoutés -> %s (%d octets)' % (len(syms), dst, os.path.getsize(dst)))

if __name__ == '__main__':
    main()
