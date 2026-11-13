#!/usr/bin/env python3
"""Retouche du game.swf d'origine de Snake (Muxxu) pour KotionTwin.

Le SWF de l'archive a été compilé avec -D dev : en mode « browser » il remplace
les données du serveur par 200 cartes tirées au hasard, ouvre l'écran de tournoi
(draft) et redirige « Rejouer » vers un fichier local du développeur.
Trois retouches de bytecode :
  1. Main.main : saut par-dessus le bloc #if dev du mode browser ; les données
     (collection de cartes) et l'adresse « dom » viennent alors des flashvars.
  2. Game.sendInfos : appel ExternalInterface.call("ktSnakeEnd", score) au
     début de l'envoi de fin de partie, pour enregistrer le score sur le site.
  3. Game.toggleReplay (touche S de debug) neutralisé.
Usage : patch_game.py game.swf sortie.swf
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from abc_patch import swf_read, swf_write, u30, Abc, replace_body
from abcdump import ABC, R, OPS

def find_method(a, cls, meth):
    for i, ins in enumerate(a.inst):
        if a.mname(ins['name']) != cls: continue
        for t in ins['traits'] + a.cls[i]['traits']:
            if 'method' in t and a.mname(t['name']) == meth: return t['method']
    raise KeyError(cls + '.' + meth)

def instrs(a, code):
    """Liste (offset, opcode, octets) des instructions."""
    r = R(code); out = []
    while r.p < len(code):
        st = r.p; op = r.u8(); args = OPS[op][1]
        for c in args:
            if c in 'msiduf': r.u30()
            elif c in 'bB': r.u8()
            elif c == 'o': r.s24()
            elif c == 'L':
                r.s24(); n = r.u30(); [r.s24() for _ in range(n + 1)]
        out.append((st, op, bytes(code[st:r.p])))
    return out

def body_header(data, pos):
    r = R(data, pos[0]); vals = [r.u30() for _ in range(6)]
    return vals, r.p  # (method, max_stack, locals, init_scope, max_scope, code_len), début du code

def main(src, dst):
    ver, header, tags = swf_read(src)
    ti = max((i for i, t in enumerate(tags) if t[0] in (72, 82)), key=lambda i: len(tags[i][1]))
    code, data = tags[ti]
    prefix = b''
    if code == 82:
        e = data.index(b'\0', 4); prefix = data[:e + 1]; data = data[e + 1:]
    data = bytearray(data)
    a = ABC(bytes(data))

    # 1. Main.main : jump de « initproperty domain_ = file:///… » vers le test bdata._draft
    m = find_method(a, 'Main_', 'main_')
    body = a.methods[m]['body']; ins = instrs(a, body)
    s_dev = a.strs.index('file:///F:/mesdocs/projets/muxxu/games/snake/clients/arene/bin/index.html')
    k = next(j for j, (o, op, b) in enumerate(ins) if op == 0x2c and R(b, 1).u30() == s_dev)
    start = ins[k - 1][0]                       # getlex Main_ avant le pushstring
    # cible : « getlex Main_ ; getproperty bdata_ ; getproperty _draft ; coerce_a ; pushnull » suivi du if
    tgt = None
    for j in range(k, len(ins) - 4):
        if ins[j][1] == 0x60 and ins[j+1][1] == 0x66 and ins[j+2][1] == 0x66 and \
           a.mname(R(ins[j+2][2], 1).u30()) == '_draft' and ins[j+4][1] == 0x20:
            tgt = ins[j][0]; break
    assert tgt, 'cible _draft introuvable'
    (_, _, _, _, _, clen), cstart = body_header(data, a.body_pos[m])
    jmp = bytes([0x10]) + (tgt - (start + 4)).to_bytes(3, 'little', signed=True)
    data[cstart + start:cstart + start + 4] = jmp
    print('Main.main : jump %d -> %d' % (start, tgt))

    # 2. Game.sendInfos : ExternalInterface.call("ktSnakeEnd", score) en tête
    abc = Abc(bytes(data))
    s_cb = abc.add_string('ktSnakeEnd'); data = bytearray(abc.data)
    a = ABC(bytes(data))
    m = find_method(a, 'Game_', 'sendInfos_')
    body = a.methods[m]['body']; ins = instrs(a, body)
    # séquence existante « findproperty score_ ; getproperty score_ ; pushbyte 0 ; getproperty [rt] »
    j = next(j for j, (o, op, b) in enumerate(ins) if op == 0x5e and a.mname(R(b, 1).u30()) == 'score_')
    score_seq = b''.join(x[2] for x in ins[j:j + 4])
    # getlex ExternalInterface / callpropvoid call 2 : copiés d'une méthode qui les utilise déjà
    ei = call = None
    for mm in a.methods:
        c = mm['body']
        if not c: continue
        ii = instrs(a, c)
        for p in range(len(ii) - 3):
            if ii[p][1] == 0x60 and a.mname(R(ii[p][2], 1).u30()) == 'flash.external.ExternalInterface' and ii[p+3][1] == 0x4f:
                ei, call = ii[p][2], ii[p+3][2]; break
        if ei: break
    assert ei
    k = next(j for j, (o, op, b) in enumerate(ins) if op == 0x2c)  # premier pushstring (après les init)
    at = ins[k][0]
    inject = ei + bytes([0x2c]) + u30(s_cb) + score_seq + call
    (_, ms, lc, isd, msd, clen), cstart = body_header(data, a.body_pos[m])
    newcode = body[:at] + inject + body[at:]
    # pas de saut qui traverse le point d'insertion vers l'arrière dans ce préambule
    data = bytearray(replace_body(bytes(data), m, newcode, ms + 4, lc, isd, msd))
    print('Game.sendInfos : %d octets injectés à %d' % (len(inject), at))

    # 3. Game.toggleReplay (touche S, outil de dev) : sans effet, sinon la fin de
    #    partie enregistre un replay au lieu d'afficher le bilan.
    a = ABC(bytes(data))
    m = find_method(a, 'Game_', 'toggleReplay_')
    (_, ms, lc, isd, msd, clen), cstart = body_header(data, a.body_pos[m])
    data = bytearray(replace_body(bytes(data), m, bytes([0x47]), ms, lc, isd, msd))
    print('Game.toggleReplay neutralisé')

    tags[ti] = [code, prefix + bytes(data)]
    swf_write(dst, ver, header, tags)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
