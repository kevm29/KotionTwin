#!/usr/bin/env python3
"""Branche les bruitages ajoutés par KotionTwin sur games/alphabounce/game.swf.

Le jeu d'origine est muet : Sound.MUTE vaut true et le seul son prévu (« bank.wav », rebond
sur la raquette) n'a jamais été livré. Ce script ajoute, après le code principal du jeu, un
petit code AVM1 qui prévient la page (ExternalInterface.call('ktSnd', quoi)) :

  - Sound.play(lien)        → ktSnd(lien)    (seul appel : « bank.wav », rebond sur la raquette)
  - Block.explode()         → ktSnd('brick') (brique détruite)
  - Option.apply()          → ktSnd('bonus') (capsule ou objet ramassé)

La page games/alphabounce/index.html joue alors les sons MP3 correspondants.
Les classes et méthodes sont désignées par leurs noms obfusqués dans game.swf, retrouvés
en désassemblant le SWF (tools/swfdis.py) et en comparant avec les sources Haxe :

  Sound = '2F}HL' (méthode play non obfusquée), Block = '525w=' (explode = ';-[;H'),
  Option = '(izm (' (apply = ',_9t').

    python3 -I src/alphabounce/sounds_hook.py games/alphabounce/game.swf
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import avm1
from avm1 import Asm

MARK = 'ktSoundHook'
SOUND, BLOCK, EXPLODE, OPTION, APPLY = '2F}HL', '525w=', ';-[;H', '(izm (', ',_9t'

def notify(a, what):
    """flash.external.ExternalInterface.call('ktSnd', what)"""
    a.call('flash.external.ExternalInterface.call', 'ktSnd', what)

def wrap(a, cls, meth, what, keep):
    # proto.__kt_meth = proto[meth] ; proto[meth] = function(){ notify; return this.__kt_meth.apply(this, arguments) }
    a.get(cls + '.prototype').push(keep).get(cls + '.prototype').push(meth).op('GetMember').op('SetMember')
    body = Asm()
    notify(body, what)
    body.get('arguments').get('this').push(2).get('this').push(keep).op('GetMember').push('apply').op('CallMethod').op('Return')
    a.get(cls + '.prototype').push(meth).func('', [], body).op('SetMember')

def code():
    a = Asm()
    play = Asm()
    play.call('flash.external.ExternalInterface.call', 'ktSnd', lambda s: s.get('link'))
    a.get(SOUND).push('play').func('', ['link', 'vol'], play).op('SetMember')
    wrap(a, BLOCK, EXPLODE, 'brick', '__ktExplode')
    wrap(a, OPTION, APPLY, 'bonus', '__ktApply')
    a.set(f'_global.{MARK}', lambda s: s.push(True))
    return a

path = sys.argv[1]
swf = avm1.read_swf(path)
if any(c == 12 and MARK.encode() in d for c, d in swf['tags']):
    print('déjà patché'); sys.exit(0)
# juste après le gros DoAction qui définit les classes du jeu
i = max(range(len(swf['tags'])), key=lambda k: len(swf['tags'][k][1]) if swf['tags'][k][0] == 12 else -1)
swf['tags'].insert(i + 1, avm1.do_action(code()))
avm1.write_swf(path, swf)
print('bruitages branchés sur', path)
