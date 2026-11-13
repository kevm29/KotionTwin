#!/usr/bin/env python3
"""Génère KtAssets.hx : intègre au SWF les fichiers d'un dossier d'assets OpenFL
et les enregistre dans flash.Assets (remplaçant d'openfl.Assets pour la cible Flash).
usage: gen_assets.py <sortie.hx> <prefixe_id>=<dossier> [...] [--font id=fichier.ttf ...] [--exclude motif]"""
import os, sys, re, fnmatch
out = sys.argv[1]
roots, fonts, excl = [], [], []
args = sys.argv[2:]
i = 0
while i < len(args):
    a = args[i]
    if a == '--font': fonts.append(args[i+1].split('=', 1)); i += 2; continue
    if a == '--exclude': excl.append(args[i+1]); i += 2; continue
    roots.append(a.split('=', 1)); i += 1
cls, reg = [], []
n = 0
def ident(s): return re.sub(r'[^A-Za-z0-9_]', '_', s)
for prefix, d in roots:
    d = os.path.abspath(d)
    for dp, dn, fs in os.walk(d):
        dn.sort()
        for f in sorted(fs):
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, d).replace(os.sep, '/')
            aid = (prefix + '/' + rel) if prefix else rel
            if any(fnmatch.fnmatch(rel, e) or fnmatch.fnmatch(f, e) for e in excl): continue
            ext = f.rsplit('.', 1)[-1].lower()
            n += 1; c = 'A%d_%s' % (n, ident(f))[:60]
            if ext in ('png', 'jpg', 'jpeg', 'gif'):
                cls.append('@:bitmap("%s") class %s extends flash.display.BitmapData {}' % (p, c))
                reg.append('\t\tflash.Assets.bitmaps.set("%s", function() return new %s(0, 0));' % (aid, c))
            elif ext == 'mp3':
                cls.append('@:sound("%s") class %s extends flash.media.Sound {}' % (p, c))
                reg.append('\t\tflash.Assets.sounds.set("%s", function() return new %s());' % (aid, c))
            elif ext in ('ogg', 'wav', 'ttf', 'otf', 'swf'):
                continue
            else:
                cls.append('@:file("%s") class %s extends flash.utils.ByteArray {}' % (p, c))
                reg.append('\t\tflash.Assets.bytes.set("%s", function() return new %s());' % (aid, c))
for fid, fp in fonts:
    n += 1; c = 'F%d_%s' % (n, ident(fid))
    cls.append('@:font("%s", " -~\u00A0-\u017F\u2019\u2026\u20AC") class %s extends flash.text.Font {}' % (os.path.abspath(fp), c))
    reg.append('\t\tflash.text.Font.registerFont(%s); flash.Assets.fonts.set("%s", function() return new %s());' % (c, fid, c))
with open(out, 'w') as o:
    o.write('// Fichier généré par gen_assets.py — ne pas modifier.\n')
    o.write('\n'.join(cls) + '\n\nclass KtAssets {\n\tstatic var done = false;\n\tpublic static function init() {\n\t\tif( done ) return; done = true;\n')
    o.write('\n'.join(reg) + '\n\t}\n}\n')
print(n, 'fichiers')
