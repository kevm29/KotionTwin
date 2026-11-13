#!/usr/bin/env python3
"""Construit les jeux Frutiparc de KotionTwin à partir de l'archive WebGamesArchives.

Usage : python3 platforms/frutiparc/build.py <chemin vers WebGamesArchives/Frutiparc/Games> [id ...]

Pour chaque jeu : copie les fichiers utiles dans games/<id>/ et compile l'hôte Frusion
(platforms/frutiparc/frusion-host.as, via tools/as1c.py) aux dimensions et à la cadence du jeu.
"""
import os, sys, shutil, struct, subprocess, zlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

GAMES = {
    'fp-kaluga': dict(src='kaluga', w=700, h=480, fps=40, game='full.swf', files={
        'full.swf': 'full.swf',
        'map/challenge.swf': 'map/challenge.swf', 'map/dawn.swf': 'map/dawn.swf', 'map/field.swf': 'map/field.swf',
        'map/forest.swf': 'map/forest.swf', 'map/mordor.swf': 'map/mordor.swf', 'map/olympic_a.swf': 'map/olympic_a.swf',
        'map/squirrel.swf': 'map/squirrel.swf',
        'anim/intro.swf': 'anim/intro/intro.swf', 'anim/credits.swf': 'anim/credits/credits.swf',
    }),
    'fp-burningkiwi': dict(src='burningKiwi', w=350, h=350, fps=40, game='racer.swf', files={
        **{f: f for f in ['racer.swf', 'intro.swf', 'bkMenu.mp3']},
        **{f'track0{i}.swf': f'track0{i}.swf' for i in range(6)}, 'track99.swf': 'track99.swf',
        **{f'bk0{i}.mp3': f'bk0{i}.mp3' for i in range(5)},
    }),
    # Les SWF de ces jeux n'existaient que sous forme de bibliothèques séparées (assemblées par swfmake
    # chez Motion Twin) : on les fusionne avec tools/swfmerge.py.
    'fp-miniwave2': dict(src='miniWave2', w=240, h=240, fps=40, game='game.swf', files={},
        merge=('miniWave2.swf', ['lib.swf', 'gfx.swf', 'decor.swf', 'bumdum.swf'], '240x240')),
    'fp-minitroll': dict(src='miniTroll', w=240, h=240, fps=40, game='game.swf', files={},
        merge=('swf/root.swf', ['swf/gfx.swf'], None), 
        # build de développement : Manager.CHEAT = 2 affichait la barre de triche ; on la remet à 0
        patch=[(b'\x96\x08\x00\x09\x00\x02\x07\x02\x00\x00\x00', b'\x96\x08\x00\x09\x00\x02\x07\x00\x00\x00\x00')]),  # push 'Manager_CHEAT', 2
}

def patch_swf(path, patches):
    raw = open(path, 'rb').read()
    body = zlib.decompress(raw[8:]) if raw[:3] == b'CWS' else raw[8:]
    for old, new in patches:
        assert len(old) == len(new) and body.count(old) == 1, old
        body = body.replace(old, new)
    open(path, 'wb').write(b'CWS' + raw[3:8] + zlib.compress(body, 9))

def swf_len(p):
    """Longueur annoncée dans l'en-tête (= getBytesTotal() pour un SWF compressé)."""
    with open(p, 'rb') as f: return struct.unpack('<I', f.read(8)[4:8])[0]

def build(arch, gid, cfg):
    out = os.path.join(ROOT, 'games', gid)
    os.makedirs(out, exist_ok=True)
    sizes = []
    if 'merge' in cfg:
        base, libs, size = cfg['merge']; src = os.path.join(arch, cfg['src'])
        cmd = [sys.executable, '-I', os.path.join(ROOT, 'tools', 'swfmerge.py')]
        if size: cmd += ['--size', size]
        subprocess.check_call(cmd + [os.path.join(src, base), os.path.join(out, cfg['game'])] + [os.path.join(src, l) for l in libs])
    if 'patch' in cfg: patch_swf(os.path.join(out, cfg['game']), cfg['patch'])
    for dst, src in cfg['files'].items():
        s = os.path.join(arch, cfg['src'], src); d = os.path.join(out, dst)
        os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copyfile(s, d)
        if dst.endswith('.swf'): sizes.append(f'{dst}:{swf_len(s)}')
    subprocess.check_call([sys.executable, '-I', os.path.join(ROOT, 'tools', 'as1c.py'),
                           os.path.join(ROOT, 'platforms', 'frutiparc', 'frusion-host.as'), os.path.join(out, 'host.swf'),
                           '--width', str(cfg['w']), '--height', str(cfg['h']), '--fps', str(cfg['fps']),
                           '--define', 'GAME=' + cfg['game'], '--define', 'ID=' + gid, '--define', 'SIZES=' + ','.join(sizes)])
    print(gid, 'ok')

if __name__ == '__main__':
    arch = sys.argv[1]; ids = sys.argv[2:] or list(GAMES)
    for gid in ids: build(arch, gid, GAMES[gid])
