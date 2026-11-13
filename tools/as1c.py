#!/usr/bin/env python3
"""as1c : petit compilateur ActionScript 1 (sous-ensemble JavaScript) vers SWF AVM1.

Écrit pour KotionTwin afin de produire les hôtes des jeux Frutiparc sans MTASC ni Flash.
Usage : as1c.py source.as sortie.swf [--width 240 --height 240 --fps 40 --version 7 --bg ffffff]

Langage pris en charge : var, function (déclaration et expression), if/else, while, do/while,
for(;;), for (k in o), break, continue, return, switch simple, opérateurs JS usuels
(arithmétique, comparaison, logique, binaire, ternaire, typeof, delete, new, instanceof),
littéraux objet/tableau, ++/-- et affectations composées. Les variables déclarées avec var dans
une fonction sont locales (defineLocal) ; le reste suit la résolution de portée AVM1.
"""
import re, struct, sys, zlib, argparse

# ---------------------------------------------------------------- lexer
TOK = re.compile(r'''
 (?P<ws>\s+|//[^\n]*|/\*.*?\*/)
|(?P<num>0[xX][0-9a-fA-F]+|\d+\.\d*(?:[eE][-+]?\d+)?|\.\d+(?:[eE][-+]?\d+)?|\d+(?:[eE][-+]?\d+)?)
|(?P<str>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')
|(?P<id>[A-Za-z_$][A-Za-z0-9_$]*)
|(?P<op>>>>=|===|!==|>>>|<<=|>>=|\+\+|--|&&|\|\||==|!=|<=|>=|\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<|>>|[{}()\[\];,.?:~!<>=+\-*/%&|^])
''', re.S | re.X)
KEYWORDS = {'var', 'function', 'if', 'else', 'while', 'do', 'for', 'in', 'return', 'break', 'continue',
            'new', 'typeof', 'delete', 'true', 'false', 'null', 'undefined', 'this', 'switch', 'case',
            'default', 'instanceof'}

def unescape(s):
    out = []; i = 0
    while i < len(s):
        c = s[i]
        if c == '\\':
            i += 1; c = s[i]
            if c == 'n': out.append('\n')
            elif c == 't': out.append('\t')
            elif c == 'r': out.append('\r')
            elif c == 'u': out.append(chr(int(s[i+1:i+5], 16))); i += 4
            elif c == 'x': out.append(chr(int(s[i+1:i+3], 16))); i += 2
            else: out.append(c)
        else: out.append(c)
        i += 1
    return ''.join(out)

def lex(src):
    toks = []; pos = 0
    while pos < len(src):
        m = TOK.match(src, pos)
        if not m: raise SyntaxError(f'caractère inattendu {src[pos]!r} ligne {src.count(chr(10), 0, pos)+1}')
        k = m.lastgroup; v = m.group(k); line = src.count('\n', 0, pos) + 1; pos = m.end()
        if k == 'ws': continue
        if k == 'num': toks.append(('num', float(int(v, 16)) if v[:2].lower() == '0x' else float(v), line))
        elif k == 'str': toks.append(('str', unescape(v[1:-1]), line))
        elif k == 'id': toks.append(('kw' if v in KEYWORDS else 'id', v, line))
        else: toks.append(('op', v, line))
    toks.append(('eof', None, -1))
    return toks

# ---------------------------------------------------------------- parser (AST = tuples)
BIN = [['||'], ['&&'], ['|'], ['^'], ['&'], ['==', '!=', '===', '!=='], ['<', '>', '<=', '>=', 'instanceof', 'in'],
       ['<<', '>>', '>>>'], ['+', '-'], ['*', '/', '%']]
ASSIGN = {'=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=', '>>>='}

class Parser:
    def __init__(self, toks): self.t = toks; self.i = 0
    def peek(self, k=0): return self.t[self.i + k]
    def nxt(self): t = self.t[self.i]; self.i += 1; return t
    def at(self, v, kind=None):
        t = self.peek(); return t[1] == v and t[0] in (('op', 'kw') if kind is None else (kind,))
    def eat(self, v):
        t = self.nxt()
        if t[1] != v or t[0] not in ('op', 'kw'): raise SyntaxError(f'attendu {v!r}, trouvé {t[1]!r} ligne {t[2]}')
        return t
    def opt(self, v):
        if self.at(v): self.i += 1; return True
        return False
    def ident(self):
        t = self.nxt()
        if t[0] != 'id': raise SyntaxError(f'identifiant attendu, trouvé {t[1]!r} ligne {t[2]}')
        return t[1]

    def program(self):
        body = []
        while self.peek()[0] != 'eof': body.append(self.stmt())
        return body

    def block(self):
        if self.opt('{'):
            body = []
            while not self.opt('}'): body.append(self.stmt())
            return ('block', body)
        return self.stmt()

    def stmt(self):
        t = self.peek()
        if t[1] == '{' and t[0] == 'op': return self.block()
        if t[1] == ';' and t[0] == 'op': self.i += 1; return ('block', [])
        if t[0] == 'kw':
            k = t[1]
            if k == 'var': self.i += 1; s = self.vardecl(); self.opt(';'); return s
            if k == 'function' and self.peek(1)[0] == 'id':
                self.i += 1; name = self.ident(); params, body = self.funcrest(); return ('fundecl', name, params, body)
            if k == 'if':
                self.i += 1; self.eat('('); c = self.expr(); self.eat(')'); a = self.block(); b = None
                if self.opt('else'): b = self.block()
                return ('if', c, a, b)
            if k == 'while':
                self.i += 1; self.eat('('); c = self.expr(); self.eat(')'); return ('while', c, self.block())
            if k == 'do':
                self.i += 1; b = self.block(); self.eat('while'); self.eat('('); c = self.expr(); self.eat(')'); self.opt(';')
                return ('dowhile', b, c)
            if k == 'for':
                self.i += 1; self.eat('(')
                # for (var k in o) / for (k in o)
                j = self.i
                isvar = self.opt('var')
                if self.peek()[0] == 'id' and self.peek(1)[1] == 'in':
                    name = self.ident(); self.eat('in'); o = self.expr(); self.eat(')')
                    return ('forin', name, isvar, o, self.block())
                self.i = j
                init = None
                if not self.at(';'):
                    init = self.vardecl(noin=True) if self.opt('var') else ('expr', self.expr())
                self.eat(';'); cond = None if self.at(';') else self.expr(); self.eat(';')
                step = None if self.at(')') else self.expr(); self.eat(')')
                return ('for', init, cond, step, self.block())
            if k == 'return':
                self.i += 1; e = None
                if not self.at(';') and not self.at('}'): e = self.expr()
                self.opt(';'); return ('return', e)
            if k in ('break', 'continue'): self.i += 1; self.opt(';'); return (k,)
            if k == 'switch':
                self.i += 1; self.eat('('); d = self.expr(); self.eat(')'); self.eat('{'); cases = []
                while not self.opt('}'):
                    if self.opt('default'): self.eat(':'); test = None
                    else: self.eat('case'); test = self.expr(); self.eat(':')
                    body = []
                    while not (self.at('case') or self.at('default') or self.at('}')): body.append(self.stmt())
                    cases.append((test, body))
                return ('switch', d, cases)
        e = self.expr(); self.opt(';'); return ('expr', e)

    def vardecl(self, noin=False):
        decls = []
        while True:
            n = self.ident(); v = None
            if self.opt('='): v = self.assign(noin)
            decls.append((n, v))
            if not self.opt(','): break
        return ('var', decls)

    def funcrest(self):
        self.eat('('); params = []
        while not self.opt(')'):
            params.append(self.ident()); self.opt(',')
        self.eat('{'); body = []
        while not self.opt('}'): body.append(self.stmt())
        return params, body

    def expr(self):
        e = self.assign()
        while self.opt(','): e = ('seq', e, self.assign())
        return e

    def assign(self, noin=False):
        lhs = self.cond(noin)
        t = self.peek()
        if t[0] == 'op' and t[1] in ASSIGN:
            self.i += 1; rhs = self.assign(noin)
            if lhs[0] not in ('name', 'member'): raise SyntaxError(f'affectation invalide ligne {t[2]}')
            return ('assign', t[1], lhs, rhs)
        return lhs

    def cond(self, noin):
        c = self.binary(0, noin)
        if self.opt('?'):
            a = self.assign(noin); self.eat(':'); b = self.assign(noin); return ('cond', c, a, b)
        return c

    def binary(self, lvl, noin):
        if lvl == len(BIN): return self.unary()
        e = self.binary(lvl + 1, noin)
        while True:
            t = self.peek()
            if t[0] in ('op', 'kw') and t[1] in BIN[lvl] and not (noin and t[1] == 'in'):
                self.i += 1; e = ('bin', t[1], e, self.binary(lvl + 1, noin))
            else: return e

    def unary(self):
        t = self.peek()
        if t[0] == 'op' and t[1] in ('!', '-', '+', '~'): self.i += 1; return ('unary', t[1], self.unary())
        if t[0] == 'op' and t[1] in ('++', '--'): self.i += 1; return ('preinc', t[1], self.unary())
        if t[0] == 'kw' and t[1] in ('typeof', 'delete'): self.i += 1; return (t[1], self.unary())
        e = self.postfix()
        t = self.peek()
        if t[0] == 'op' and t[1] in ('++', '--'): self.i += 1; return ('postinc', t[1], e)
        return e

    def postfix(self):
        if self.at('new', 'kw'):
            self.i += 1; callee = self.primary()
            while True:
                if self.opt('.'): callee = ('member', callee, ('lit', self.nxt()[1]))
                elif self.opt('['): callee = ('member', callee, self.expr()); self.eat(']')
                else: break
            args = self.args() if self.at('(') else []
            e = ('new', callee, args)
        else: e = self.primary()
        while True:
            if self.opt('.'): e = ('member', e, ('lit', self.nxt()[1]))
            elif self.opt('['): e = ('member', e, self.expr()); self.eat(']')
            elif self.at('('): e = ('call', e, self.args())
            else: return e

    def args(self):
        self.eat('('); a = []
        while not self.opt(')'):
            a.append(self.assign()); self.opt(',')
        return a

    def primary(self):
        t = self.nxt()
        if t[0] == 'num': return ('lit', t[1])
        if t[0] == 'str': return ('lit', t[1])
        if t[0] == 'id': return ('name', t[1])
        if t[0] == 'kw':
            if t[1] == 'true': return ('lit', True)
            if t[1] == 'false': return ('lit', False)
            if t[1] == 'null': return ('lit', None)
            if t[1] == 'undefined': return ('undef',)
            if t[1] == 'this': return ('this',)
            if t[1] == 'function':
                name = self.ident() if self.peek()[0] == 'id' else ''
                params, body = self.funcrest(); return ('func', name, params, body)
        if t[1] == '(' and t[0] == 'op': e = self.expr(); self.eat(')'); return e
        if t[1] == '[' and t[0] == 'op':
            items = []
            while not self.opt(']'):
                items.append(self.assign()); self.opt(',')
            return ('array', items)
        if t[1] == '{' and t[0] == 'op':
            props = []
            while not self.opt('}'):
                k = self.nxt(); self.eat(':'); props.append((str(k[1]) if k[0] != 'num' else fmtnum(k[1]), self.assign())); self.opt(',')
            return ('object', props)
        raise SyntaxError(f'expression inattendue {t[1]!r} ligne {t[2]}')

INTRINSICS = {'trace', 'loadMovieNum', 'loadMovie', 'unloadMovieNum', 'getURL', 'fscommand'}

def fmtnum(v): return str(int(v)) if v == int(v) else repr(v)

# ---------------------------------------------------------------- code generation
OP = dict(add2=0x47, sub=0x0B, mul=0x0C, div=0x0D, mod=0x3F, eq=0x49, seq=0x66, lt=0x48, gt=0x67, not_=0x12,
          band=0x60, bor=0x61, bxor=0x62, shl=0x63, shr=0x64, ushr=0x65, getvar=0x1C, setvar=0x1D, getmem=0x4E,
          setmem=0x4F, callfn=0x3D, callmeth=0x52, newobj=0x40, newmeth=0x53, initarr=0x42, initobj=0x43,
          pop=0x17, dup=0x4C, swap=0x4D, ret=0x3E, typeof=0x44, delete=0x3A, delete2=0x3B, deflocal=0x3C,
          deflocal2=0x41, enum2=0x55, instanceof=0x54, inc=0x50, dec=0x51, tonum=0x4A)
BINOPS = {'+': ['add2'], '-': ['sub'], '*': ['mul'], '/': ['div'], '%': ['mod'], '==': ['eq'], '!=': ['eq', 'not_'],
          '===': ['seq'], '!==': ['seq', 'not_'], '<': ['lt'], '>': ['gt'], '<=': ['gt', 'not_'], '>=': ['lt', 'not_'],
          '&': ['band'], '|': ['bor'], '^': ['bxor'], '<<': ['shl'], '>>': ['shr'], '>>>': ['ushr'],
          'instanceof': ['instanceof']}

class Code:
    """Flux d'actions avec étiquettes résolues à la fin."""
    def __init__(self): self.items = []; self.nlab = 0
    def label(self): self.nlab += 1; return self.nlab
    def mark(self, l): self.items.append(('mark', l))
    def op(self, name): self.items.append(('raw', bytes([OP[name]])))
    def act(self, code, payload=b''): self.items.append(('raw', bytes([code]) + struct.pack('<H', len(payload)) + payload))
    def jump(self, kind, l): self.items.append((kind, l))  # 'jump' 0x99 / 'if' 0x9D
    def push(self, *vals):
        p = b''
        for v in vals:
            if v is None: p += b'\x02'
            elif v is UNDEF: p += b'\x03'
            elif isinstance(v, Reg): p += b'\x04' + bytes([v.n])
            elif isinstance(v, bool): p += b'\x05' + bytes([v])
            elif isinstance(v, float) or isinstance(v, int):
                if float(v).is_integer() and -2**31 <= v < 2**31: p += b'\x07' + struct.pack('<i', int(v))
                else:
                    d = struct.pack('<d', float(v)); p += b'\x06' + d[4:] + d[:4]
            else: p += b'\x00' + str(v).encode('utf-8') + b'\0'
        self.act(0x96, p)
    def func(self, name, params, body_bytes):
        p = name.encode('utf-8') + b'\0' + struct.pack('<H', len(params))
        for a in params: p += a.encode('utf-8') + b'\0'
        p += struct.pack('<H', len(body_bytes))
        self.act(0x9B, p); self.items.append(('raw', body_bytes))
    def assemble(self):
        # deux passes : tailles fixes (sauts = 5 octets)
        pos = {}; off = 0
        for it in self.items:
            if it[0] == 'mark': pos[it[1]] = off
            elif it[0] == 'raw': off += len(it[1])
            else: off += 5
        out = b''; off = 0
        for it in self.items:
            if it[0] == 'mark': continue
            if it[0] == 'raw': out += it[1]; off += len(it[1]); continue
            off += 5
            out += bytes([0x99 if it[0] == 'jump' else 0x9D]) + struct.pack('<Hh', 2, pos[it[1]] - off)
        return out

class Reg:
    def __init__(self, n): self.n = n
class _U: pass
UNDEF = _U()

class Gen:
    def __init__(self): self.loops = []
    def compile_body(self, stmts, infunc):
        c = Code(); self.c = c; saved = self.loops; self.loops = []; self.infunc = infunc
        # hissage des fonctions déclarées
        for s in stmts:
            if s[0] == 'fundecl': self.fundecl(s)
        for s in stmts:
            if s[0] != 'fundecl': self.stmt(s)
        self.loops = saved
        return c
    def fundecl(self, s):
        _, name, params, body = s
        b = self.funcbytes(params, body)
        if self.infunc:
            self.c.push(name); self.c.func('', params, b); self.c.op('deflocal')
        else:
            self.c.func(name, params, b)
    def funcbytes(self, params, body):
        saved = (self.c, self.infunc)
        sub = self.compile_body(body, True).assemble()
        self.c, self.infunc = saved
        return sub
    def stmt(self, s):
        c = self.c; k = s[0]
        if k == 'block':
            for x in s[1]:
                if x[0] == 'fundecl': self.fundecl(x)
            for x in s[1]:
                if x[0] != 'fundecl': self.stmt(x)
        elif k == 'fundecl': self.fundecl(s)
        elif k == 'var':
            for n, v in s[1]:
                if self.infunc:
                    c.push(n)
                    if v is None: c.op('deflocal2')
                    else: self.expr(v); c.op('deflocal')
                elif v is not None:
                    c.push(n); self.expr(v); c.op('setvar')
        elif k == 'expr': self.expr(s[1], discard=True)
        elif k == 'if':
            le = c.label(); lend = c.label()
            self.expr(s[1]); c.op('not_'); c.jump('if', le)
            self.stmt(s[2])
            if s[3] is not None: c.jump('jump', lend)
            c.mark(le)
            if s[3] is not None: self.stmt(s[3]); c.mark(lend)
        elif k == 'while':
            top = c.label(); end = c.label()
            c.mark(top); self.expr(s[1]); c.op('not_'); c.jump('if', end)
            self.loops.append((end, top, False)); self.stmt(s[2]); self.loops.pop()
            c.jump('jump', top); c.mark(end)
        elif k == 'dowhile':
            top = c.label(); cont = c.label(); end = c.label()
            c.mark(top); self.loops.append((end, cont, False)); self.stmt(s[1]); self.loops.pop()
            c.mark(cont); self.expr(s[2]); c.jump('if', top); c.mark(end)
        elif k == 'for':
            _, init, cond, step, body = s
            if init is not None: self.stmt(init)
            top = c.label(); cont = c.label(); end = c.label()
            c.mark(top)
            if cond is not None: self.expr(cond); c.op('not_'); c.jump('if', end)
            self.loops.append((end, cont, False)); self.stmt(body); self.loops.pop()
            c.mark(cont)
            if step is not None: self.expr(step, discard=True)
            c.jump('jump', top); c.mark(end)
        elif k == 'forin':
            _, name, isvar, obj, body = s
            top = c.label(); end = c.label(); brk = c.label()
            self.expr(obj); c.op('enum2')
            c.mark(top)
            c.act(0x87, bytes([0]))  # storeRegister r0
            c.push(None); c.op('eq'); c.jump('if', end)
            c.push(name, Reg(0)); c.op('deflocal' if (isvar and self.infunc) else 'setvar')
            self.loops.append((brk, top, True)); self.stmt(body); self.loops.pop()
            c.jump('jump', top)
            # sortie anticipée : vider la pile d'énumération
            c.mark(brk)
            c.push(None); c.op('eq'); c.op('not_'); c.jump('if', brk)
            c.mark(end)
        elif k == 'break':
            end, _, isenum = self.loops[-1]; c.jump('jump', end)
        elif k == 'continue':
            l = self.loops[-1]; c.jump('jump', l[1])
        elif k == 'return':
            if s[1] is None: c.push(UNDEF)
            else: self.expr(s[1])
            # sortir proprement des for..in englobants
            for (end, top, isenum) in reversed(self.loops):
                if isenum:
                    # valeur de retour au sommet : on la met de côté dans r1
                    c.act(0x87, bytes([1])); c.op('pop')
                    l = c.label(); c.mark(l); c.push(None); c.op('eq'); c.op('not_'); c.jump('if', l)
                    c.push(Reg(1))
            c.op('ret')
        elif k == 'switch':
            _, d, cases = s
            end = c.label(); labels = [c.label() for _ in cases]
            self.expr(d); c.act(0x87, bytes([0])); c.op('pop')
            dflt = None
            for i, (test, body) in enumerate(cases):
                if test is None: dflt = labels[i]; continue
                c.push(Reg(0)); self.expr(test); c.op('seq'); c.jump('if', labels[i])
            c.jump('jump', dflt if dflt is not None else end)
            self.loops.append((end, self.loops[-1][1] if self.loops else end, False))
            for i, (test, body) in enumerate(cases):
                c.mark(labels[i])
                for x in body: self.stmt(x)
            self.loops.pop(); c.mark(end)
        else: raise ValueError(k)

    def expr(self, e, discard=False):
        c = self.c; k = e[0]
        if k == 'assign':
            self.assign(e, discard); return
        if k in ('preinc', 'postinc'):
            self.incdec(e, discard); return
        if k == 'lit': c.push(e[1])
        elif k == 'undef': c.push(UNDEF)
        elif k == 'this': c.push('this'); c.op('getvar')
        elif k == 'name': c.push(e[1]); c.op('getvar')
        elif k == 'member': self.expr(e[1]); self.expr(e[2]); c.op('getmem')
        elif k == 'call' and e[1][0] == 'name' and e[1][1] in INTRINSICS:
            name, args = e[1][1], e[2]
            if name == 'trace': self.expr(args[0]); c.items.append(('raw', b'\x26'))
            elif name == 'loadMovieNum':
                self.expr(args[0]); c.push('_level'); self.expr(args[1]); c.op('add2'); c.act(0x9A, bytes([0]))
            elif name == 'loadMovie':
                self.expr(args[0]); self.expr(args[1]); c.act(0x9A, bytes([0x40]))
            elif name == 'unloadMovieNum':
                c.push(''); c.push('_level'); self.expr(args[0]); c.op('add2'); c.act(0x9A, bytes([0]))
            elif name == 'getURL':
                self.expr(args[0])
                if len(args) > 1: self.expr(args[1])
                else: c.push('')
                c.act(0x9A, bytes([0]))
            elif name == 'fscommand':
                c.push('FSCommand:'); self.expr(args[0]); c.op('add2')
                if len(args) > 1: self.expr(args[1])
                else: c.push('')
                c.act(0x9A, bytes([0]))
            c.push(UNDEF)
        elif k == 'call':
            args = e[2]
            for a in reversed(args): self.expr(a)
            c.push(len(args)); f = e[1]
            if f[0] == 'name': c.push(f[1]); c.op('callfn')
            elif f[0] == 'member': self.expr(f[1]); self.expr(f[2]); c.op('callmeth')
            else: self.expr(f); c.push(UNDEF); c.op('callmeth')
        elif k == 'new':
            args = e[2]
            for a in reversed(args): self.expr(a)
            c.push(len(args)); f = e[1]
            if f[0] == 'name': c.push(f[1]); c.op('newobj')
            elif f[0] == 'member': self.expr(f[1]); self.expr(f[2]); c.op('newmeth')
            else: self.expr(f); c.push(UNDEF); c.op('newmeth')
        elif k == 'func':
            c.func(e[1], e[2], self.funcbytes(e[2], e[3]))
        elif k == 'array':
            for a in reversed(e[1]): self.expr(a)
            c.push(len(e[1])); c.op('initarr')
        elif k == 'object':
            for n, v in e[1]: c.push(n); self.expr(v)
            c.push(len(e[1])); c.op('initobj')
        elif k == 'seq': self.expr(e[1], discard=True); self.expr(e[2])
        elif k == 'cond':
            lt = c.label(); lend = c.label()
            self.expr(e[1]); c.jump('if', lt); self.expr(e[3]); c.jump('jump', lend)
            c.mark(lt); self.expr(e[2]); c.mark(lend)
        elif k == 'unary':
            if e[1] == '!': self.expr(e[2]); c.op('not_')
            elif e[1] == '-': c.push(0); self.expr(e[2]); c.op('sub')
            elif e[1] == '+': self.expr(e[2]); c.op('tonum')
            elif e[1] == '~': self.expr(e[2]); c.push(-1); c.op('bxor')
        elif k == 'typeof': self.expr(e[1]); c.op('typeof')
        elif k == 'delete':
            t = e[1]
            if t[0] == 'member': self.expr(t[1]); self.expr(t[2]); c.op('delete')
            elif t[0] == 'name': c.push(t[1]); c.op('delete2')
            else: c.push(True)
        elif k == 'bin':
            o = e[1]
            if o in ('&&', '||'):
                l = c.label(); self.expr(e[2]); c.op('dup')
                if o == '&&': c.op('not_')
                c.jump('if', l); c.op('pop'); self.expr(e[3]); c.mark(l)
            elif o == 'in':
                # k in o  ->  o[k] !== undefined (approximation)
                self.expr(e[3]); self.expr(e[2]); c.op('getmem'); c.push(UNDEF); c.op('seq'); c.op('not_')
            else:
                self.expr(e[2]); self.expr(e[3])
                for x in BINOPS[o]: c.op(x)
        else: raise ValueError(k)
        if discard: c.op('pop')

    def ref(self, t):
        """Empile la référence (nom ou obj+clé) ; renvoie (getter, setter) en ops."""
        if t[0] == 'name': self.c.push(t[1]); return 'var'
        self.expr(t[1]); self.expr(t[2]); return 'mem'

    def assign(self, e, discard):
        c = self.c; _, op, lhs, rhs = e
        kind = self.ref(lhs)
        if op != '=':
            # dupliquer la référence pour relire la valeur
            if kind == 'var': c.push(lhs[1]); c.op('getvar')
            else: self.expr(lhs[1]); self.expr(lhs[2]); c.op('getmem')
            self.expr(rhs)
            for x in BINOPS[op[:-1]]: c.op(x)
        else: self.expr(rhs)
        if not discard: c.act(0x87, bytes([0]))
        c.op('setvar' if kind == 'var' else 'setmem')
        if not discard: c.push(Reg(0))

    def incdec(self, e, discard):
        c = self.c; k, op, t = e
        kind = self.ref(t)
        if kind == 'var': c.push(t[1]); c.op('getvar')
        else: self.expr(t[1]); self.expr(t[2]); c.op('getmem')
        c.op('tonum')
        if k == 'postinc' and not discard: c.act(0x87, bytes([1]))
        c.op('inc' if op == '++' else 'dec')
        if k == 'preinc' and not discard: c.act(0x87, bytes([1]))
        c.op('setvar' if kind == 'var' else 'setmem')
        if not discard: c.push(Reg(1))

# ---------------------------------------------------------------- SWF writer
def rect_bytes(w, h):
    vals = [0, int(w * 20), 0, int(h * 20)]
    nb = max(v.bit_length() for v in vals) + 1
    bits = format(nb, '05b') + ''.join(format(v, f'0{nb}b') for v in vals)
    bits += '0' * (-len(bits) % 8)
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))

def tag(code, data):
    if len(data) < 63: return struct.pack('<H', (code << 6) | len(data)) + data
    return struct.pack('<HI', (code << 6) | 63, len(data)) + data

def build_swf(actions, w, h, fps, version, bg, compress=True):
    body = rect_bytes(w, h) + struct.pack('<BBH', int((fps % 1) * 256), int(fps), 1)
    body += tag(69, struct.pack('<I', 0)) if version >= 8 else b''   # FileAttributes (réseau local off)
    body += tag(9, bytes.fromhex(bg))
    body += tag(12, actions + b'\0') + tag(1, b'') + tag(0, b'')
    if compress: return b'CWS' + bytes([version]) + struct.pack('<I', len(body) + 8) + zlib.compress(body, 9)
    return b'FWS' + bytes([version]) + struct.pack('<I', len(body) + 8) + body

def compile_source(src):
    ast = Parser(lex(src)).program()
    return Gen().compile_body(ast, False).assemble()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('out')
    ap.add_argument('--width', type=float, default=240); ap.add_argument('--height', type=float, default=240)
    ap.add_argument('--fps', type=float, default=40); ap.add_argument('--version', type=int, default=7)
    ap.add_argument('--bg', default='ffffff'); ap.add_argument('--define', action='append', default=[],
                    help='NOM=valeur : remplace %%NOM%% dans la source')
    a = ap.parse_args()
    src = open(a.src, encoding='utf-8').read()
    for d in a.define:
        k, v = d.split('=', 1); src = src.replace('%' + k + '%', v)
    open(a.out, 'wb').write(build_swf(compile_source(src), a.width, a.height, a.fps, a.version, a.bg))

if __name__ == '__main__':
    main()
