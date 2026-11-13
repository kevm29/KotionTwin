#!/usr/bin/env python3
"""Fabrique les vignettes du catalogue (assets/covers/<id>.webp) à partir de data/covers.json.

Chaque entrée de data/covers.json indique dans "from" l'image d'origine, relative à la racine
de l'archive WebGamesArchives (capture d'époque, logo, écran de jeu…), ou "swf:<chemin>" quand
la vignette est une capture du SWF rendu par Ruffle (capture recadrée, rangée dans le dossier --shots
sous le nom <id>.png), ou "icon:<chemin dans le dépôt>" pour agrandir en pixel art une icône d'époque
trop petite (icônes 16×16 d'Arkadeo) sur un fond aux couleurs de la collection.

Usage : python3 -I tools/make_covers.py <archive> [--only id1,id2] [--shots <dossier de captures SWF>]

Les images sont recadrées en 4:3 (480×360). Une image trop large ou trop haute (logo, affiche)
est centrée en entier sur un fond flou tiré d'elle-même, pour ne pas la couper.
"""
import json, os, sys
from PIL import Image, ImageFilter, ImageStat

W, H = 480, 360

def compose(im):
    im = im.convert('RGBA')
    # fond blanc sous la transparence pour les logos
    if im.getextrema()[3][0] < 255:
        bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg
    im = im.convert('RGB')
    ar = im.width / im.height
    small = im.width < W * 0.6
    resample = Image.NEAREST if small else Image.LANCZOS
    if 1.05 <= ar <= 1.6:
        s = max(W / im.width, H / im.height)
        r = im.resize((max(W, round(im.width * s)), max(H, round(im.height * s))), resample)
        x, y = (r.width - W) // 2, (r.height - H) // 2
        return r.crop((x, y, x + W, y + H))
    # fond flou + image entière
    s = max(W / im.width, H / im.height)
    bg = im.resize((round(im.width * s) + 2, round(im.height * s) + 2), Image.BILINEAR)
    x, y = (bg.width - W) // 2, (bg.height - H) // 2
    bg = bg.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(18))
    bg = Image.blend(bg, Image.new('RGB', (W, H), (0, 0, 0)), 0.35)
    s = min(W * 0.92 / im.width, H * 0.92 / im.height)
    fg = im.resize((round(im.width * s), round(im.height * s)), resample)
    bg.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2))
    return bg

COLLECTION_COLORS = {
    'kadokado': ('#ff9f1c', '#7a3b00'), 'arkadeo': ('#29b6f6', '#0b3a66'), 'cafejeux': ('#c98a5a', '#4a2510'),
    'frutiparc': ('#7ccf3a', '#1f4d0b'), 'muxxu': ('#ff5c8a', '#5c0f2a'), 'motiontwin': ('#a77bff', '#2c1466'),
}

def icon_cover(path, collection):
    a, b = (tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in COLLECTION_COLORS.get(collection, ('#ffcc33', '#3a2a00')))
    bg = Image.new('RGB', (W, H))
    px = bg.load()
    for y in range(H):
        for x in range(W):
            t = (x / W + y / H) / 2
            px[x, y] = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    ic = Image.open(path).convert('RGBA')
    k = (H * 2 // 3) // max(ic.size)
    big = ic.resize((ic.width * k, ic.height * k), Image.NEAREST)
    shadow = Image.new('RGBA', big.size, (0, 0, 0, 0))
    shadow.putalpha(big.getchannel('A').point(lambda v: v * 0.35))
    out = bg.convert('RGBA')
    x, y = (W - big.width) // 2, (H - big.height) // 2
    out.alpha_composite(shadow, (x + 8, y + 10))
    out.alpha_composite(big, (x, y))
    return out.convert('RGB')

def main():
    args = sys.argv[1:]
    arch = args[0]
    only = set(args[args.index('--only') + 1].split(',')) if '--only' in args else None
    shots = args[args.index('--shots') + 1] if '--shots' in args else None
    covers = json.load(open('data/covers.json'))
    games = {g['id']: g for g in json.load(open('data/games.json'))['games']}
    os.makedirs('assets/covers', exist_ok=True)
    for gid, c in covers['games'].items():
        if only and gid not in only:
            continue
        src = c['from']
        if src.startswith('icon:'):
            icon_cover(src[5:], games[gid]['collection']).save(c['src'], 'WEBP', quality=85, method=6)
            print(gid, '←', src)
            continue
        if src.startswith('swf:'):
            if not shots:
                continue
            path = os.path.join(shots, gid + '.png')
        else:
            path = os.path.join(arch, src)
        im = compose(Image.open(path))
        if sum(ImageStat.Stat(im).var) / 3 < 100:
            print('ATTENTION image presque unie :', gid, file=sys.stderr)
        im.save(c['src'], 'WEBP', quality=82, method=6)
        print(gid, '←', src)

if __name__ == '__main__':
    main()
