#!/usr/bin/env python3
"""Petit assembleur AVM1 (Flash 5-8) et outils de réécriture de SWF.

Sert à greffer du code « hôte » sur des SWF d'origine (Pioupiouz, Dinocard…)
sans recompiler leurs sources : le code est écrit en Python avec la classe Asm,
puis inséré sous forme de tag DoAction dans le SWF.

    from avm1 import Asm, Reg, UNDEF, read_swf, write_swf, tag
    a = Asm()
    a.push('trace', 'bonjour').call_function(1)...  (voir platforms/flash8/README.md)
"""
import struct, zlib

class Reg:
    def __init__(self, n): self.n = n
class _Undef: pass
UNDEF = _Undef()

OPS = {
 'NextFrame':0x04,'PrevFrame':0x05,'Play':0x06,'Stop':0x07,'Add':0x0A,'Subtract':0x0B,'Multiply':0x0C,
 'Divide':0x0D,'Equals':0x0E,'Less':0x0F,'And':0x10,'Or':0x11,'Not':0x12,'Pop':0x17,'ToInteger':0x18,
 'GetVariable':0x1C,'SetVariable':0x1D,'StringAdd':0x21,'GetProperty':0x22,'SetProperty':0x23,'Trace':0x26,
 'GetTime':0x34,'Delete':0x3A,'Delete2':0x3B,'DefineLocal':0x3C,'CallFunction':0x3D,'Return':0x3E,
 'Modulo':0x3F,'NewObject':0x40,'DefineLocal2':0x41,'InitArray':0x42,'InitObject':0x43,'TypeOf':0x44,
 'Add2':0x47,'Less2':0x48,'Equals2':0x49,'ToNumber':0x4A,'ToString':0x4B,'PushDuplicate':0x4C,
 'StackSwap':0x4D,'GetMember':0x4E,'SetMember':0x4F,'Increment':0x50,'Decrement':0x51,'CallMethod':0x52,
 'NewMethod':0x53,'InstanceOf':0x54,'Enumerate2':0x55,'BitAnd':0x60,'BitOr':0x61,'StrictEquals':0x66,
 'Greater':0x67,'Extends':0x69,
}

def _s(x): return x.encode('latin-1') + b'\0'

class Asm:
    def __init__(self):
        self.parts = []      # bytes ou ('jump'|'if', label)
        self.labels = {}
        self._n = 0
    # -- bas niveau
    def raw(self, b): self.parts.append(bytes(b)); return self
    def op(self, name): return self.raw([OPS[name]])
    def _long(self, code, payload): return self.raw(bytes([code]) + struct.pack('<H', len(payload)) + payload)
    def push(self, *vals):
        out = b''
        for v in vals:
            if isinstance(v, Reg): out += bytes([4, v.n])
            elif v is UNDEF: out += b'\x03'
            elif v is None: out += b'\x02'
            elif isinstance(v, bool): out += bytes([5, 1 if v else 0])
            elif isinstance(v, int) and -2**31 <= v < 2**31: out += b'\x07' + struct.pack('<i', v)
            elif isinstance(v, (int, float)):
                d = struct.pack('<d', float(v)); out += b'\x06' + d[4:] + d[:4]
            elif isinstance(v, str): out += b'\x00' + _s(v)
            else: raise TypeError(v)
        return self._long(0x96, out)
    def store(self, r): return self._long(0x87, bytes([r]))
    def label(self, name): self.parts.append(('label', name)); return self
    def jump(self, name): self.parts.append(('jump', name)); return self
    def if_(self, name): self.parts.append(('if', name)); return self
    def newlabel(self):
        self._n += 1; return f'L{self._n}'
    def goto_label(self, name): return self._long(0x8C, _s(name))
    def func2(self, name, params, body, regs=None, flags=0):
        """DefineFunction2. params : liste de noms (stockés dans les registres 1..n).
        flags : 0x01 preload this… ici on n'utilise que des noms (pas de préchargement)."""
        code = body.assemble()
        regs = regs if regs is not None else len(params) + 4
        pl = b''.join(bytes([i + 1]) + _s(p) for i, p in enumerate(params))
        payload = _s(name) + struct.pack('<HBH', len(params), regs, flags) + pl + struct.pack('<H', len(code))
        self._long(0x8E, payload)
        return self.raw(code)
    def func(self, name, params, body):
        """DefineFunction classique : paramètres accessibles par GetVariable(nom)."""
        code = body.assemble()
        payload = _s(name) + struct.pack('<H', len(params)) + b''.join(_s(p) for p in params) + struct.pack('<H', len(code))
        self._long(0x9B, payload)
        return self.raw(code)
    def __getattr__(self, name):
        if name in OPS: return lambda: self.op(name)
        raise AttributeError(name)
    # -- macros
    def get(self, path):
        """Empile la valeur de a.b.c"""
        first, *rest = path.split('.')
        if first.startswith('r') and first[1:].isdigit(): self.push(Reg(int(first[1:])))
        else: self.push(first).op('GetVariable')
        for r in rest: self.push(r).op('GetMember')
        return self
    def set(self, path, emit):
        """path = valeur ; emit(asm) empile la valeur."""
        *objs, last = path.split('.')
        if objs:
            self.get('.'.join(objs)); self.push(last); emit(self); self.op('SetMember')
        else:
            self.push(last); emit(self); self.op('SetVariable')
        return self
    def call(self, path, *args, pop=True):
        """Appelle a.b.f(args) ; chaque arg est une valeur poussable ou un callable(asm)."""
        for a in reversed(args):
            a(self) if callable(a) else self.push(a)
        self.push(len(args))
        *objs, last = path.split('.')
        if objs:
            self.get('.'.join(objs)); self.push(last); self.op('CallMethod')
        else:
            self.push(last); self.op('CallFunction')
        if pop: self.op('Pop')
        return self
    def new(self, cls, *args):
        for a in reversed(args):
            a(self) if callable(a) else self.push(a)
        self.push(len(args), cls).op('NewObject')
        return self
    def end(self): return self.raw(b'\0')
    # -- assemblage
    def assemble(self):
        # 1re passe : positions
        pos = 0; offs = {}
        sizes = []
        for p in self.parts:
            if isinstance(p, tuple):
                if p[0] == 'label': offs[p[1]] = pos; sizes.append(0)
                else: sizes.append(5); pos += 5
            else: sizes.append(len(p)); pos += len(p)
        out = b''; pos = 0
        for p, sz in zip(self.parts, sizes):
            if isinstance(p, tuple):
                if p[0] == 'label': continue
                tgt = offs[p[1]]; rel = tgt - (pos + 5)
                out += bytes([0x99 if p[0] == 'jump' else 0x9D]) + struct.pack('<Hh', 2, rel)
                pos += 5
            else:
                out += p; pos += len(p)
        return out

# ---------------------------------------------------------------- SWF
def read_swf(path):
    b = open(path, 'rb').read()
    if b[:3] == b'CWS': body = zlib.decompress(b[8:])
    elif b[:3] == b'FWS': body = b[8:]
    else: raise ValueError('SWF non géré')
    version = b[3]
    nbits = body[0] >> 3; rl = (5 + 4 * nbits + 7) // 8
    rect = body[:rl]; rate, count = struct.unpack('<HH', body[rl:rl+4])
    p = rl + 4; tags = []
    while p < len(body):
        th = struct.unpack('<H', body[p:p+2])[0]; p += 2
        code, ln = th >> 6, th & 63
        if ln == 63: ln = struct.unpack('<I', body[p:p+4])[0]; p += 4
        tags.append((code, body[p:p+ln])); p += ln
        if code == 0: break
    return {'version': version, 'rect': rect, 'rate': rate, 'count': count, 'tags': tags}

def rect_bytes(w, h):
    vals = [0, w * 20, 0, h * 20]
    nbits = max(v.bit_length() for v in vals) + 1
    bits = format(nbits, '05b') + ''.join(format(v, f'0{nbits}b') for v in vals)
    bits += '0' * (-len(bits) % 8)
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))

def tag(code, data):
    if len(data) < 63 and code not in (6, 21, 35, 20, 36, 90):
        return struct.pack('<H', (code << 6) | len(data)) + data
    return struct.pack('<HI', (code << 6) | 63, len(data)) + data

def write_swf(path, swf, compress=True):
    body = swf['rect'] + struct.pack('<HH', swf['rate'], swf['count'])
    body += b''.join(tag(c, d) for c, d in swf['tags'])
    if not swf['tags'] or swf['tags'][-1][0] != 0: body += tag(0, b'')
    total = len(body) + 8
    hdr = struct.pack('<I', total)
    if compress: data = b'CWS' + bytes([swf['version']]) + hdr + zlib.compress(body, 9)
    else: data = b'FWS' + bytes([swf['version']]) + hdr + body
    open(path, 'wb').write(data)

def do_action(asm): return (12, asm.assemble() + b'\0')
