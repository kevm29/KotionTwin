#!/usr/bin/env python3
"""Génère data/games.json à partir de l'archive motion-twin/WebGamesArchives.

Usage : python3 -I tools/build_catalog.py /chemin/vers/WebGamesArchives

Le script ne fait qu'inventorier : il conserve les champs déjà édités à la main
dans data/games.json (status, entry, description, …) et n'ajoute que les jeux
manquants. Il copie une vignette (capture d'origine) dans games/<id>/thumb.*.
"""
import json, os, sys, shutil, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, '..', 'WebGamesArchives')
OUT = os.path.join(ROOT, 'data', 'games.json')

def slug(s):
    s = s.lower().replace('é', 'e').replace('è', 'e')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')

COLLECTIONS = {
    'kadokado':  {'name': 'KadoKado', 'years': '2004-2010', 'about': "Portail de mini-jeux d'arcade à score, jouables en une partie de quelques minutes."},
    'arkadeo':   {'name': 'Arkadeo', 'years': '2013-2014', 'about': "Salle d'arcade en ligne : mini-jeux Flash AS3 à progression et objectifs."},
    'cafejeux':  {'name': 'CaféJeux', 'years': '2007', 'about': "Jeux de plateau et d'adresse en duel, joués dans un café virtuel."},
    'frutiparc': {'name': 'Frutiparc', 'years': '2004', 'about': "Le bureau virtuel de Motion Twin et ses jeux « Frusion »."},
    'muxxu':     {'name': 'Muxxu', 'years': '2009-2011', 'about': "Plateforme de jeux de Motion Twin : arcade, gestion et duels."},
    'motiontwin':{'name': 'Jeux Motion Twin', 'years': '2005-2015', 'about': "Les jeux web autonomes du studio."},
}

# Titres lisibles pour les dossiers dont le nom est technique.
TITLES = {
    'Cooking Lili': 'Cooking Lili', 'Iron Chouquette': 'Iron Chouquette', 'Judo Commando': 'Judo Commando',
    'Kanji_Gaiden': 'Kanji Gaiden', 'KanjiAdventure': 'Kanji Adventure', 'KanjiNightmare': 'Kanji Nightmare',
    'Mini-race': 'Mini-Race', 'Red Raid': 'Red Raid', 'Tout-Caen': 'Tout-Caen', 'TwinSpirit': 'Twin Spirit',
    'abcrevolution': 'ABC Revolution', 'alchimie2': 'Alchimie 2', 'opalusFactory': 'Opalus Factory',
    'HappyPtyTank': 'Happy Pty Tank', 'PuzzleSnake': 'Puzzle Snake', 'SchizoFuzz': 'Schizo Fuzz',
    'TortugaQix': 'Tortuga Qix', 'Tianan Man': 'Tianan Man', 'Kinker Surprise': 'Kinker Surprise',
    'Cosmo-Crash': 'Cosmo Crash', 'f1champion': 'F1 Champion', 'kaskade2': 'Kaskade 2',
    'brutal teenage crisis': 'Brutal Teenage Crisis', 'battleSheep': 'Battle Sheep', 'charlotteQuest': "Charlotte's Quest",
    'greenWitch': 'Green Witch', 'rockFaller': 'Rock Faller (Arkadeo)', 'fafi360': 'Fafi 360', 'nosushi': 'No Sushi',
    'power4': 'Puissance 4', 'laferme': 'La Ferme', 'hordes': 'Hordes (CaféJeux)', 'opalus': 'Opalus (CaféJeux)',
    'grapiz': 'Grapiz', 'burningKiwi': 'Burning Kiwi', 'frutibandas': 'Frutibandas', 'miniFever': 'Mini Fever',
    'miniTroll': 'Mini Troll', 'miniWave2': 'Mini Wave 2', 'motionBall2': 'Motion Ball 2', 'snake3': 'Snake 3',
    'swapou2': 'Swapou 2', 'Hotel': 'CroqueMotel', 'LaBrute': 'La Brute', 'Fever': 'Fever', 'Kube': 'Kube',
    'Kingdom': 'Kingdom', 'Intrusion': 'Intrusion', 'Odyssey': 'Odyssey', 'Snake': 'Snake',
}

# Jeux autonomes (racine de l'archive) : année, techno, plan de restauration.
STANDALONE = {
    'Alphabounce':   (2007, 'Haxe 2 → Flash 8 (AVM1)', 'ruffle-shim', "Client game.swf présent ; simuler le protocole serveur (com/Protocol.hx) pour un mode solo."),
    'Dinocard':      (2006, 'MotionTypes (.mt) → Flash 7/8', 'ruffle-shim', "code.swf/temple.swf compilés présents ; adversaire et decks à simuler côté navigateur."),
    'Dinoparc':      (2005, 'Site web (images + XML)', 'portage', "Aucun client Flash : jeu web côté serveur à réimplémenter en JS à partir des XML et images."),
    'DinoRPG':       (2007, 'Haxe 2 serveur + clients Flash 8', 'portage', "Logique serveur (Haxe/neko) à porter en JS ; réutiliser les SWF combat/carte/donjon."),
    'Galaxy55':      (2012, 'Haxe → Flash 11 (AS3)', 'portage', "Alpha multijoueur : explore.swf présent, monde et serveur à simuler."),
    'Hordes':        (2008, 'Haxe 2 serveur + clients Flash 8', 'portage', "Jeu de survie multijoueur côté serveur : version solo à réimplémenter, SWF carte/exploration réutilisables."),
    'LaBourinette':  (2011, 'Haxe serveur + site', 'portage', "Pas de SWF : simulation de match (src/game) à porter en JS."),
    'Miniville':     (2007, 'Haxe 2 → Flash 8 (AVM1)', 'ruffle-shim', "client.swf présent ; simuler l'API serveur de la ville."),
    'MonsterHotel':  (2015, 'Haxe 3 + OpenFL/h3d', 'recompilation', "Aucun binaire : recompiler le client OpenFL en HTML5 (ou Flash puis Ruffle)."),
    'Mush':          (2012, 'Haxe serveur + client iso AS3', 'portage', "Jeu multijoueur côté serveur ; client iso à recompiler, partie solo à concevoir."),
    'Naturalchimie2':(2010, 'Haxe 2 → Flash 8 (AVM1)', 'recompilation', "game.swf (code) absent : recompiler fla/game/src avec gfx.swf/sound.swf."),
    'Pioupiouz':     (2006, 'ActionScript 2 → Flash 7/8', 'ruffle-shim', "pioupiouz.swf/code.swf présents + niveaux XML/SQL : brancher le chargement des niveaux."),
    'Rockfaller':    (2015, 'Haxe 3 (Flash/mobile)', 'recompilation', "Client à recompiler (src + assets + sons) ; seul loading.swf est compilé."),
    'SkyWar':        (2009, 'Haxe 2 → Flash 8 (AVM1)', 'portage', "Stratégie multijoueur : client.swf à recompiler et serveur à simuler."),
    'Socrate':       (2005, 'ActionScript (FLA)', 'portage', "Socratomancie : boule magique ; recoder en HTML5 depuis code.as/sentence.as."),
    'TeacherStory':  (2013, 'Haxe → Flash 11 (AS3)', 'portage', "Client classe à recompiler, logique serveur à simuler."),
    'Uppercup':      (2014, 'Haxe → AIR/Flash 11', 'recompilation', "client.swf absent : recompiler (gfx.swf + sources), cible Flash puis Ruffle ou HTML5."),
}
STANDALONE_TITLES = {'Alphabounce': 'Alphabounce', 'Dinocard': 'Dinocard', 'Dinoparc': 'Dinoparc', 'DinoRPG': 'DinoRPG',
    'Galaxy55': 'Galaxy 55', 'Hordes': 'Hordes', 'LaBourinette': 'La Bourinette', 'Miniville': 'Miniville',
    'MonsterHotel': 'Monster Hotel', 'Mush': 'Mush', 'Naturalchimie2': 'Naturalchimie 2', 'Pioupiouz': 'Pioupiouz',
    'Rockfaller': 'Rockfaller Journey', 'SkyWar': 'SkyWar', 'Socrate': 'Socratomancie', 'TeacherStory': 'Teacher Story',
    'Uppercup': 'Uppercup Football'}

MUXXU = {
    'Fever':     (2010, 'Haxe → Flash 9 (AS3)', 'ruffle-shim', "game.swf présent (fr/en/es/de) ; simuler les appels serveur (îles, objets)."),
    'Snake':     (2010, 'Haxe → Flash 9 (AS3)', 'recompilation', "arène game.swf à vérifier/recompiler ; cartes et quêtes à simuler."),
    'Odyssey':   (2011, 'Haxe → Flash 10 (AS3)', 'recompilation', "all.swf (graphismes) présent, client à recompiler, serveur à simuler."),
    'Kube':      (2010, 'Haxe → Flash 10/11 (AS3)', 'recompilation', "Monde voxel : client à recompiler, génération de monde locale."),
    'Intrusion': (2009, 'Haxe 2 → Flash 8 (AVM1)', 'recompilation', "_gfx.swf/_cinematics.swf présents, _code.swf à recompiler."),
    'LaBrute':   (2010, 'Haxe 2 → Flash 8 (AVM1)', 'portage', "Combats calculés côté serveur : porter la simulation, réutiliser gfx.swf."),
    'Kingdom':   (2009, 'Haxe → Flash 9 (AS3)', 'portage', "Jeu de gestion multijoueur : clients carte/bataille à recompiler, serveur à simuler."),
    'Hotel':     (2011, 'Haxe → Flash 10 (AS3)', 'portage', "CroqueMotel : client à recompiler, logique de l'hôtel à simuler."),
}

def find_thumb(d):
    cands = []
    for root, dirs, files in os.walk(d):
        for f in files:
            fl = f.lower()
            if re.match(r'^(sc|sc0|sc1|sc2|teaser|apercu|minisreen|logo|r_.*_a)\.(gif|jpe?g|png)$', fl) or fl in ('judo-commando.gif',):
                cands.append(os.path.join(root, f))
        if root.count(os.sep) - d.count(os.sep) >= 1:
            dirs[:] = [x for x in dirs if x == 'icons']
    pri = lambda p: (0 if '/sc' in p.lower() else 1 if 'r_' in p else 2, len(p))
    return sorted(cands, key=pri)[0] if cands else None

def swfs(d):
    out = []
    for root, dirs, files in os.walk(d):
        for f in files:
            if f.lower().endswith('.swf'):
                out.append(os.path.relpath(os.path.join(root, f), ARCH))
    return sorted(out)

def count(d, exts):
    n = 0
    for root, dirs, files in os.walk(d):
        n += sum(1 for f in files if f.lower().endswith(exts))
    return n

def entry(id_, title, coll, src, year, tech, plan, note):
    d = os.path.join(ARCH, src)
    return {
        'id': id_, 'title': title, 'collection': coll, 'year': year,
        'source': src, 'tech': tech, 'plan': plan, 'status': 'a-restaurer', 'notes': note,
        'stats': {'swf': len(swfs(d)), 'hx': count(d, ('.hx',)), 'as': count(d, ('.as', '.mt')),
                  'images': count(d, ('.png', '.jpg', '.jpeg', '.gif')),
                  'sons': count(d, ('.mp3', '.wav', '.ogg'))},
        'entry': None, 'thumb': None, 'description': '',
    }

def build():
    games = []
    kk = os.path.join(ARCH, 'KadoKado', 'Games')
    for g in sorted(os.listdir(kk), key=str.lower):
        if g == 'api' or not os.path.isdir(os.path.join(kk, g)): continue
        d = os.path.join(kk, g); hx = count(d, ('.hx',))
        if hx:
            tech, plan, note = 'Haxe 2 → Flash 8 (AVM1)', 'ruffle-shim', "game.swf + gfx.swf : fournir l'API KKApi via un loader de remplacement."
        else:
            tech, plan, note = 'MotionTypes/AS → Flash 6-8 (AVM1)', 'ruffle-shim', "SWF compilés (code/temple/gfx) : fournir l'API KadoKado historique via un loader de remplacement."
        if not swfs(d): plan, note = 'recompilation', "Aucun SWF compilé : recompiler les sources."
        games.append(entry('kk-' + slug(g), TITLES.get(g, g[:1].upper() + g[1:]), 'kadokado', f'KadoKado/Games/{g}', None, tech, plan, note))
    ak = os.path.join(ARCH, 'Arkadeo', 'games')
    for g in sorted(os.listdir(ak), key=str.lower):
        games.append(entry('ak-' + slug(g), TITLES.get(g, g[:1].upper() + g[1:]), 'arkadeo', f'Arkadeo/games/{g}', None,
                           'Haxe → Flash 10/11 (AS3)', 'ruffle-shim', "game.swf (AS3) : fournir l'API Arkadeo (api.AKApi, absente de l'archive)."))
    cj = os.path.join(ARCH, 'CafeJeux', 'games')
    for g in sorted(os.listdir(cj), key=str.lower):
        has = os.path.exists(os.path.join(cj, g, 'swf', 'game.swf'))
        games.append(entry('cj-' + slug(g), TITLES.get(g, g[:1].upper() + g[1:]), 'cafejeux', f'CafeJeux/games/{g}', 2007,
                           'Haxe 2 → Flash 8 (AVM1)', 'ruffle-shim' if has else 'recompilation',
                           ("game.swf présent" if has else "game.swf absent (seul gfx.swf) : recompiler") + " ; jeu à 2 joueurs : recréer l'API CaféJeux (../api absent) pour un duel local ou contre une IA."))
    fp = os.path.join(ARCH, 'Frutiparc', 'Games')
    for g in sorted(os.listdir(fp), key=str.lower):
        has = bool(swfs(os.path.join(fp, g)))
        games.append(entry('fp-' + slug(g), TITLES.get(g, g), 'frutiparc', f'Frutiparc/Games/{g}', 2004,
                           'ActionScript 1/2 → Flash 6-7 (AVM1)', 'ruffle-shim' if has else 'recompilation',
                           ("SWF présents" if has else "Pas de SWF, sources .as + .fla : recompiler (MTASC/Haxe) ou reconstruire") + " ; simuler l'API Frusion (Frutiparc/frusion)."))
    for g, (y, t, p, n) in MUXXU.items():
        games.append(entry('mx-' + slug(TITLES[g]), TITLES[g], 'muxxu', f'Muxxu/{g}', y, t, p, n))
    for g, (y, t, p, n) in STANDALONE.items():
        games.append(entry(slug(STANDALONE_TITLES[g]), STANDALONE_TITLES[g], 'motiontwin', g, y, t, p, n))
    return games

def main():
    old = {}
    if os.path.exists(OUT):
        old = {g['id']: g for g in json.load(open(OUT, encoding='utf-8'))['games']}
    games = build()
    for g in games:
        o = old.get(g['id'])
        if o:  # garder les champs édités par les threads de restauration
            for k in ('status', 'entry', 'description', 'thumb', 'year', 'title', 'plan', 'notes', 'credits', 'controls'):
                if o.get(k) not in (None, '', 'a-restaurer'): g[k] = o[k]
        if not g['thumb']:
            t = find_thumb(os.path.join(ARCH, g['source']))
            if t:
                dst = os.path.join('games', g['id'], 'thumb' + os.path.splitext(t)[1].lower())
                os.makedirs(os.path.join(ROOT, os.path.dirname(dst)), exist_ok=True)
                shutil.copyfile(t, os.path.join(ROOT, dst))
                g['thumb'] = dst
    json.dump({'collections': COLLECTIONS, 'games': games}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(games), 'jeux ->', OUT)

main()
