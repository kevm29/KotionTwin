#!/usr/bin/env python3
"""Green Witch : réactive les sons.

Le game.swf archivé a été compilé avec « -D disableSfx » : les classes _SFX_* sont
vides et mt.deepnight.Sfx.start() commence par « return » (le code mort qui suit a
été abîmé par l'obfuscateur). On remplace le corps de Sfx.start() par :
    vol *= CHANNELS.get(channel).volume (si le canal existe)
    curPlay = sound.play(startOffset, loops, new SoundTransform(vol, pan)); volume = vol;
Les sons eux-mêmes sont ensuite ajoutés par tools/swf_add_sounds.py.

Usage : greenwitch_sfx.py entree.swf sortie.swf
"""
import sys, os
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools')
sys.path.insert(0, T)
from abc_patch import Abc, swf_read, swf_write, replace_body, u30
from abcdump import ABC

src, dst = sys.argv[1:3]
ver, header, tags = swf_read(src)
done = False
for t in tags:
    if t[0] != 72: continue
    a = ABC(t[1])
    idx = None
    for ins in a.inst:
        if a.mname(ins['name']) == 'mt_.deepnight_.Sfx_':
            for tr in ins['traits']:
                if a.mname(tr['name']) == 'start_': idx = tr['method']
    if idx is None: continue
    p = Abc(t[1])
    play = p.add_qname('', 'play')
    st = p.find_qname('flash.media', 'SoundTransform')
    sound = p.find_qname('', 'sound_'); cur = p.find_qname('', 'curPlay_'); vol = p.find_qname('', 'volume_')
    sfx = p.find_qname('mt_.deepnight_', 'Sfx_'); chans = p.find_qname('', 'CHANNELS_')
    exists = p.find_qname('', 'exists_'); get = p.find_qname('', 'get_'); chan = p.find_qname('', 'channel_')
    assert None not in (play, st, sound, cur, vol, sfx, chans, exists, get, chan)
    lookup = b'\x60' + u30(sfx) + b'\x66' + u30(chans) + b'\xd0\x66' + u30(chan)
    true_branch = lookup + b'\x46' + u30(get) + u30(1) + b'\x66' + u30(vol) + b'\xa2'   # * canal.volume
    code = (b'\xd0\x30'                       # getlocal0 pushscope
            + b'\xd2'                         # vol
            + lookup + b'\x46' + u30(exists) + u30(1)
            + b'\x12' + len(true_branch).to_bytes(3, 'little', signed=True)  # iffalse
            + true_branch
            + b'\x75\xd6'                     # convert_d setlocal2 : vol *= volume du canal
            + b'\xd0\xd2\x61' + u30(vol)      # this.volume_ = vol
            + b'\xd0'                         # this (pour curPlay_)
            + b'\xd0\x66' + u30(sound)        # this.sound_
            + b'\x62\x04'                     # startOffset
            + b'\xd1'                         # loops
            + b'\x5d' + u30(st)               # findpropstrict SoundTransform
            + b'\xd2\xd3'                     # vol, pan
            + b'\x4a' + u30(st) + u30(2)      # new SoundTransform(vol, pan)
            + b'\x46' + u30(play) + u30(3)    # sound.play(off, loops, st)
            + b'\x61' + u30(cur)              # this.curPlay_ = ...
            + b'\x47')                        # returnvoid
    t[1] = replace_body(bytes(p.data), idx, code, 8, 5, 0, 1)
    done = True
assert done, 'Sfx.start introuvable'
swf_write(dst, ver, header, tags)
print('Sfx.start réécrit ->', dst)
