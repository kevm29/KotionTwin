#!/usr/bin/env python3
"""avm1c : mini-compilateur d'un sous-ensemble d'ActionScript 1 vers du bytecode AVM1 (Flash 8).

Écrit pour KotionTwin parce que Haxe 2 / MTASC / JPEXS ne sont pas disponibles dans
l'environnement de construction. Langage pris en charge (syntaxe JavaScript) :

  var, function (déclaration et expression), if/else, while, for(;;), break, continue,
  return, expressions : littéraux (nombre, chaîne, true/false/null/undefined), objets
  {a:1}, tableaux [1,2], accès a.b / a[b], appels, new, opérateurs + - * / % == != ===
  !== < > <= >= && || ! ?: typeof, affectations = += -= *= /=, ++/-- (en instruction).

Les identifiants sont résolus dynamiquement (getVariable / setVariable / defineLocal) :
c'est le comportement d'AS1. Les chaînes sont encodées en UTF-8 (SWF 6+).

Usage : python3 avm1c.py source.as sortie.swf [--width 300 --height 320 --fps 40 --bg FFFFFF]
"""
import re, struct, sys, argparse

# ---------------------------------------------------------------- lexer
TOK = re.compile(r"""
 (?P<ws>\s+|//[^\n]*|/\*.*?\*/)
|(?P<num>0x[0-9a-fA-F]+|\d+\.\d*(?:[eE][-+]?\d+)?|\.\d+(?:[eE][-+]?\d+)?|\d+(?:[eE][-+]?\d+)?)
|(?P<str>"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')
|(?P<id>[A-Za-z_$][A-Za-z0-9_$]*)
|(?P<op>===|!==|==|!=|<=|>=|&&|\|\||\+\+|--|\+=|-=|\*=|/=|[-+*/%<>=!?:.,;(){}\[\]&|^])
""", re.S | re.X)
KEYWORDS = {'var', 'function', 'if', 'else', 'while', 'for', 'return', 'break', 'continue',
            'new', 'true', 'false', 'null', 'undefined', 'typeof', 'this', 'delete'}

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
            else: out.append(c)
        else: out.append(c)
        i += 1
    return ''.join(out)

def lex(src):
    pos = 0; toks = []
    while pos < len(src):
        m = TOK.match(src, pos)
        if not m: raise SyntaxError('caractère inattendu %r ligne %d' % (src[pos], src.count('\n', 0, pos) + 1))
        pos = m.end(); k = m.lastgroup; v = m.group(k)
        line = src.count('\n', 0, m.start()) + 1
        if k == 'ws': continue
        if k == 'num': toks.append(('num', float(int(v, 16)) if v.startswith('0x') else float(v), line))
        elif k == 'str': toks.append(('str', unescape(v[1:-1]), line))
        elif k == 'id': toks.append(('kw' if v in KEYWORDS else 'id', v, line))
        else: toks.append(('op', v, line))
    toks.append(('eof', None, 0))
    return toks

# ---------------------------------------------------------------- parser (AST = tuples)
BIN_PREC = {'||': 1, '&&': 2, '|': 3, '^': 4, '&': 5, '==': 6, '!=': 6, '===': 6, '!==': 6,
            '<': 7, '>': 7, '<=': 7, '>=': 7, '+': 9, '-': 9, '*': 10, '/': 10, '%': 10}

class Parser:
    def __init__(self, toks): self.t = toks; self.i = 0
    def peek(self, k=0): return self.t[self.i + k]
    def next(self): tok = self.t[self.i]; self.i += 1; return tok
    def at(self, v, kind=None):
        tok = self.peek(); return tok[1] == v and (kind is None or tok[0] == kind) and tok[0] in ('op', 'kw')
    def eat(self, v):
        tok = self.next()
        if tok[1] != v or tok[0] not in ('op', 'kw'): raise SyntaxError('attendu %r, trouvé %r ligne %d' % (v, tok[1], tok[2]))
        return tok
    def ident(self):
        tok = self.next()
        if tok[0] != 'id': raise SyntaxError('identifiant attendu, trouvé %r ligne %d' % (tok[1], tok[2]))
        return tok[1]

    def program(self):
        out = []
        while self.peek()[0] != 'eof': out.append(self.statement())
        return out
    def block(self):
        if self.at('{'):
            self.eat('{'); out = []
            while not self.at('}'): out.append(self.statement())
            self.eat('}'); return out
        return [self.statement()]
    def statement(self):
        tok = self.peek()
        if tok[0] == 'kw':
            v = tok[1]
            if v == 'var':
                self.next(); decls = []
                while True:
                    name = self.ident(); init = None
                    if self.at('='): self.eat('='); init = self.expr()
                    decls.append(('var', name, init))
                    if self.at(','): self.eat(','); continue
                    break
                self.semi(); return ('block', decls)
            if v == 'function' and self.peek(1)[0] == 'id':
                self.next(); name = self.ident(); params, body = self.funcrest()
                return ('fundecl', name, params, body)
            if v == 'if':
                self.next(); self.eat('('); c = self.expr(); self.eat(')'); a = self.block(); b = None
                if self.at('else'): self.eat('else'); b = self.block()
                return ('if', c, a, b)
            if v == 'while':
                self.next(); self.eat('('); c = self.expr(); self.eat(')'); return ('while', c, self.block())
            if v == 'for':
                self.next(); self.eat('(')
                init = None if self.at(';') else self.statement_nosemi()
                self.eat(';'); cond = None if self.at(';') else self.expr(); self.eat(';')
                step = None if self.at(')') else self.statement_nosemi_expr(); self.eat(')')
                return ('for', init, cond, step, self.block())
            if v == 'return':
                self.next(); e = None
                if not self.at(';') and not self.at('}'): e = self.expr()
                self.semi(); return ('return', e)
            if v == 'break': self.next(); self.semi(); return ('break',)
            if v == 'continue': self.next(); self.semi(); return ('continue',)
        if self.at('{'): return ('block', self.block())
        if self.at(';'): self.eat(';'); return ('block', [])
        s = self.statement_nosemi_expr(); self.semi(); return s
    def statement_nosemi(self):
        if self.at('var'):
            self.next(); name = self.ident(); init = None
            if self.at('='): self.eat('='); init = self.expr()
            return ('var', name, init)
        return self.statement_nosemi_expr()
    def statement_nosemi_expr(self):
        e = self.expr()
        if self.peek()[0] == 'op' and self.peek()[1] in ('=', '+=', '-=', '*=', '/='):
            op = self.next()[1]; v = self.expr()
            if op != '=': v = ('bin', op[0], e, v)
            return ('assign', e, v)
        if self.at('++') or self.at('--'):
            op = self.next()[1]
            return ('assign', e, ('bin', '+' if op == '++' else '-', e, ('num', 1.0)))
        return ('expr', e)
    def semi(self):
        if self.at(';'): self.eat(';')
    def funcrest(self):
        self.eat('('); params = []
        while not self.at(')'):
            params.append(self.ident())
            if self.at(','): self.eat(',')
        self.eat(')'); return params, self.block()

    def expr(self):
        c = self.binary(0)
        if self.at('?'):
            self.eat('?'); a = self.expr(); self.eat(':'); b = self.expr(); return ('cond', c, a, b)
        return c
    def binary(self, minp):
        left = self.unary()
        while True:
            tok = self.peek()
            if tok[0] != 'op' or tok[1] not in BIN_PREC or BIN_PREC[tok[1]] <= minp: return left
            op = self.next()[1]; right = self.binary(BIN_PREC[op])
            left = ('bin', op, left, right)
    def unary(self):
        if self.at('!'): self.eat('!'); return ('not', self.unary())
        if self.at('-'): self.eat('-'); return ('bin', '-', ('num', 0.0), self.unary())
        if self.at('typeof'): self.next(); return ('typeof', self.unary())
        if self.at('delete'):
            self.next(); e = self.unary()
            if e[0] != 'member': raise SyntaxError('delete attend a.b')
            return ('delete', e[1], e[2])
        return self.postfix()
    def postfix(self):
        tok = self.next(); k, v = tok[0], tok[1]
        if k == 'num': e = ('num', v)
        elif k == 'str': e = ('str', v)
        elif k == 'id': e = ('var', v)
        elif k == 'kw' and v == 'true': e = ('bool', True)
        elif k == 'kw' and v == 'false': e = ('bool', False)
        elif k == 'kw' and v == 'null': e = ('null',)
        elif k == 'kw' and v == 'undefined': e = ('undef',)
        elif k == 'kw' and v == 'this': e = ('var', 'this')
        elif k == 'kw' and v == 'function':
            name = self.ident() if self.peek()[0] == 'id' else ''
            params, body = self.funcrest(); e = ('func', name, params, body)
        elif k == 'kw' and v == 'new':
            target = self.postfix_noncall(); args = []
            if self.at('('): args = self.args()
            e = ('new', target, args)
        elif k == 'op' and v == '(':
            e = self.expr(); self.eat(')')
        elif k == 'op' and v == '[':
            items = []
            while not self.at(']'):
                items.append(self.expr())
                if self.at(','): self.eat(',')
            self.eat(']'); e = ('array', items)
        elif k == 'op' and v == '{':
            pairs = []
            while not self.at('}'):
                t2 = self.next(); key = t2[1] if t2[0] != 'num' else str(int(t2[1]))
                self.eat(':'); pairs.append((key, self.expr()))
                if self.at(','): self.eat(',')
            self.eat('}'); e = ('object', pairs)
        else: raise SyntaxError('expression attendue, trouvé %r ligne %d' % (v, tok[2]))
        return self.suffixes(e, True)
    def postfix_noncall(self):
        tok = self.next()
        if tok[0] != 'id': raise SyntaxError('new attend un identifiant ligne %d' % tok[2])
        return self.suffixes(('var', tok[1]), False)
    def suffixes(self, e, calls):
        while True:
            if self.at('.'):
                self.eat('.'); tok = self.next(); e = ('member', e, ('str', tok[1]))
            elif self.at('['):
                self.eat('['); k = self.expr(); self.eat(']'); e = ('member', e, k)
            elif calls and self.at('('):
                e = ('call', e, self.args())
            else: return e
    def args(self):
        self.eat('('); out = []
        while not self.at(')'):
            out.append(self.expr())
            if self.at(','): self.eat(',')
        self.eat(')'); return out

# ---------------------------------------------------------------- code generation
class Code:
    def __init__(self): self.b = bytearray(); self.fix = []; self.labels = {}; self.n = 0
    def label(self): self.n += 1; return self.n
    def mark(self, l): self.labels[l] = len(self.b)
    def op(self, code, data=b''):
        if code >= 0x80: self.b += bytes([code]) + struct.pack('<H', len(data)) + data
        else: self.b.append(code)
    def jump(self, code, l):
        self.b += bytes([code]) + struct.pack('<H', 2); self.fix.append((len(self.b), l)); self.b += b'\0\0'
    def push(self, *vals):
        d = bytearray()
        for v in vals:
            if v is None: d.append(2)
            elif v is Undef: d.append(3)
            elif isinstance(v, bool): d += bytes([5, 1 if v else 0])
            elif isinstance(v, str): d += b'\0' + v.encode('utf-8') + b'\0'
            elif isinstance(v, (int, float)) and float(v).is_integer() and -2**31 <= v < 2**31:
                d += b'\x07' + struct.pack('<i', int(v))
            else:
                x = struct.pack('<d', float(v)); d += b'\x06' + x[4:] + x[:4]
        self.op(0x96, bytes(d))
    def finish(self):
        for pos, l in self.fix:
            off = self.labels[l] - (pos + 2)
            self.b[pos:pos+2] = struct.pack('<h', off)
        return bytes(self.b)

class _U: pass
Undef = _U()

BINOPS = {'+': [0x47], '-': [0x0B], '*': [0x0C], '/': [0x0D], '%': [0x3F], '<': [0x48], '>': [0x67],
          '==': [0x49], '!=': [0x49, 0x12], '===': [0x66], '!==': [0x66, 0x12], '<=': [0x67, 0x12],
          '>=': [0x48, 0x12], '&': [0x60], '|': [0x61], '^': [0x62]}

class Gen:
    def __init__(self): self.loops = []
    def body(self, stmts):
        c = Code(); saved = self.loops; self.loops = []
        for s in stmts: self.stmt(c, s)
        self.loops = saved
        return c.finish()
    def stmt(self, c, s):
        k = s[0]
        if k == 'block':
            for x in s[1]: self.stmt(c, x)
        elif k == 'var':
            c.push(s[1])
            if s[2] is None: c.op(0x41)            # defineLocal2
            else: self.expr(c, s[2]); c.op(0x3C)   # defineLocal
        elif k == 'fundecl':
            self.func(c, s[1], s[2], s[3])
        elif k == 'expr':
            self.expr(c, s[1]); c.op(0x17)
        elif k == 'assign':
            self.assign(c, s[1], s[2])
        elif k == 'if':
            le = c.label(); lend = c.label()
            self.expr(c, s[1]); c.op(0x12); c.jump(0x9D, le)
            for x in s[2]: self.stmt(c, x)
            if s[3]:
                c.jump(0x99, lend); c.mark(le)
                for x in s[3]: self.stmt(c, x)
                c.mark(lend)
            else: c.mark(le)
        elif k == 'while':
            top = c.label(); end = c.label(); c.mark(top)
            self.expr(c, s[1]); c.op(0x12); c.jump(0x9D, end)
            self.loops.append((top, end))
            for x in s[2]: self.stmt(c, x)
            self.loops.pop(); c.jump(0x99, top); c.mark(end)
        elif k == 'for':
            if s[1]: self.stmt(c, s[1])
            top = c.label(); cont = c.label(); end = c.label(); c.mark(top)
            if s[2]: self.expr(c, s[2]); c.op(0x12); c.jump(0x9D, end)
            self.loops.append((cont, end))
            for x in s[4]: self.stmt(c, x)
            self.loops.pop(); c.mark(cont)
            if s[3]: self.stmt(c, s[3])
            c.jump(0x99, top); c.mark(end)
        elif k == 'break': c.jump(0x99, self.loops[-1][1])
        elif k == 'continue': c.jump(0x99, self.loops[-1][0])
        elif k == 'return':
            if s[1] is None: c.push(Undef)
            else: self.expr(c, s[1])
            c.op(0x3E)
        else: raise Exception('instruction inconnue ' + k)
    def assign(self, c, target, value):
        if target[0] == 'var':
            c.push(target[1]); self.expr(c, value); c.op(0x1D)
        elif target[0] == 'member':
            self.expr(c, target[1]); self.expr(c, target[2]); self.expr(c, value); c.op(0x4F)
        else: raise Exception('cible d\'affectation invalide')
    def func(self, c, name, params, body):
        code = self.body(body)
        d = name.encode('utf-8') + b'\0' + struct.pack('<H', len(params))
        for p in params: d += p.encode('utf-8') + b'\0'
        d += struct.pack('<H', len(code))
        c.op(0x9B, d); c.b += code
    def expr(self, c, e):
        k = e[0]
        if k == 'num': c.push(e[1])
        elif k == 'str': c.push(e[1])
        elif k == 'bool': c.push(e[1])
        elif k == 'null': c.push(None)
        elif k == 'undef': c.push(Undef)
        elif k == 'var': c.push(e[1]); c.op(0x1C)
        elif k == 'member': self.expr(c, e[1]); self.expr(c, e[2]); c.op(0x4E)
        elif k == 'not': self.expr(c, e[1]); c.op(0x12)
        elif k == 'typeof': self.expr(c, e[1]); c.op(0x44)
        elif k == 'delete': self.expr(c, e[1]); self.expr(c, e[2]); c.op(0x3A)
        elif k == 'bin':
            op = e[1]
            if op in ('&&', '||'):
                l = c.label(); self.expr(c, e[2]); c.op(0x4C)
                if op == '&&': c.op(0x12)
                c.jump(0x9D, l); c.op(0x17); self.expr(c, e[3]); c.mark(l)
            else:
                self.expr(c, e[2]); self.expr(c, e[3])
                for o in BINOPS[op]: c.op(o)
        elif k == 'cond':
            la = c.label(); lend = c.label()
            self.expr(c, e[1]); c.jump(0x9D, la); self.expr(c, e[3]); c.jump(0x99, lend)
            c.mark(la); self.expr(c, e[2]); c.mark(lend)
        elif k == 'array':
            for x in reversed(e[1]): self.expr(c, x)
            c.push(len(e[1])); c.op(0x42)
        elif k == 'object':
            for key, v in e[1]: c.push(key); self.expr(c, v)
            c.push(len(e[1])); c.op(0x43)
        elif k == 'func': self.func(c, e[1], e[2], e[3])
        elif k == 'call':
            for a in reversed(e[2]): self.expr(c, a)
            c.push(len(e[2])); f = e[1]
            if f[0] == 'var': c.push(f[1]); c.op(0x3D)
            elif f[0] == 'member': self.expr(c, f[1]); self.expr(c, f[2]); c.op(0x52)
            else: self.expr(c, f); c.push(Undef); c.op(0x52)
        elif k == 'new':
            for a in reversed(e[2]): self.expr(c, a)
            c.push(len(e[2])); f = e[1]
            if f[0] == 'var': c.push(f[1]); c.op(0x40)
            else: self.expr(c, f[1]); self.expr(c, f[2]); c.op(0x53)
        else: raise Exception('expression inconnue ' + k)

def compile_as(src):
    ast = Parser(lex(src)).program()
    return Gen().body(ast) + b'\0'

# ---------------------------------------------------------------- SWF writer
def tag(code, data):
    if len(data) < 63: return struct.pack('<H', (code << 6) | len(data)) + data
    return struct.pack('<HI', (code << 6) | 63, len(data)) + data

def rect(w, h):
    vals = [0, int(w * 20), 0, int(h * 20)]
    nb = max(v.bit_length() for v in vals) + 1
    bits = format(nb, '05b') + ''.join(format(v, '0%db' % nb) for v in vals)
    bits += '0' * (-len(bits) % 8)
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))

def make_swf(actions, width=300, height=320, fps=40, bg='FFFFFF', version=8):
    body = rect(width, height) + struct.pack('<BBH', int((fps % 1) * 256), int(fps), 1)
    body += tag(69, struct.pack('<I', 0x01))                       # FileAttributes : useNetwork
    body += tag(9, bytes.fromhex(bg))                               # SetBackgroundColor
    body += tag(12, actions)                                        # DoAction
    body += tag(1, b'') + tag(0, b'')
    return b'FWS' + bytes([version]) + struct.pack('<I', len(body) + 8) + body

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('out')
    ap.add_argument('--width', type=float, default=300); ap.add_argument('--height', type=float, default=320)
    ap.add_argument('--fps', type=float, default=40); ap.add_argument('--bg', default='FFFFFF')
    ap.add_argument('-D', action='append', default=[], help='NOM=valeur : remplace %%NOM%% dans la source')
    a = ap.parse_args()
    src = open(a.src, encoding='utf-8').read()
    for d in a.D:
        n, v = d.split('=', 1); src = src.replace('%' + n + '%', v)
    open(a.out, 'wb').write(make_swf(compile_as(src), a.width, a.height, a.fps, a.bg))
    print('écrit', a.out)
