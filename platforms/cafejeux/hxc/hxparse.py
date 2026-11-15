"""hxparse : lecteur d'un sous-ensemble de Haxe 2 (celui des jeux CaféJeux) pour hxc.

Écrit pour KotionTwin : Haxe 2.10 n'est pas disponible dans l'environnement de construction.
Produit un AST fait de tuples ('kind', ...). Les types sont lus puis ignorés (sauf les noms
de classes/enums), le code généré étant dynamique comme celui de Haxe pour Flash 8.
"""
import re

KEYWORDS = {'package', 'import', 'class', 'interface', 'enum', 'typedef', 'extends', 'implements',
            'var', 'function', 'return', 'if', 'else', 'while', 'do', 'for', 'in', 'break', 'continue',
            'switch', 'case', 'default', 'try', 'catch', 'throw', 'new', 'this', 'super', 'null',
            'true', 'false', 'cast', 'untyped', 'static', 'public', 'private', 'override', 'inline',
            'dynamic', 'extern', 'callback', 'f9dynamic'}

TOK = re.compile(r'''
 (?P<ws>\s+|//[^\n]*|/\*.*?\*/)
|(?P<pp>\#(?:if|elseif|else|end|error)\b)
|(?P<num>0x[0-9a-fA-F]+|\d+\.(?!\.)\d*(?:[eE][-+]?\d+)?|\d+(?:[eE][-+]?\d+)?|\.\d+)
|(?P<str>"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')
|(?P<id>[A-Za-z_$][A-Za-z0-9_$]*)
|(?P<op>>>>=|\.\.\.|===|!==|<<=|>>=|>>>|>>|==|!=|<=|>=|&&|\|\||\+\+|--|\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<|->|[-+*/%<>=!?:.,;(){}\[\]&|^~@])
''', re.S | re.X)

class HxError(Exception):
    pass

def unescape(s):
    out = []; i = 0
    while i < len(s):
        c = s[i]
        if c == '\\':
            i += 1; c = s[i]
            if c == 'n': out.append('\n')
            elif c == 't': out.append('\t')
            elif c == 'r': out.append('\r')
            elif c == 'x': out.append(chr(int(s[i+1:i+3], 16))); i += 2
            elif c == 'u': out.append(chr(int(s[i+1:i+5], 16))); i += 4
            else: out.append(c)
        else:
            out.append(c)
        i += 1
    return ''.join(out)

def lex(src, fname, defines):
    toks = []
    pos = 0
    line = 1
    raw = []
    while pos < len(src):
        m = TOK.match(src, pos)
        if not m:
            raise HxError('%s:%d: caractère inattendu %r' % (fname, line, src[pos]))
        k = m.lastgroup; v = m.group(k)
        if k != 'ws':
            raw.append((k, v, line))
        line += v.count('\n')
        pos = m.end()
    # préprocesseur #if / #elseif / #else / #end
    out = []
    stack = []  # (actif_parent, deja_pris, actif)
    active = True
    i = 0
    def cond(i):
        # lit une condition : ident, !ident, ( expr ) avec || &&
        def prim(i):
            k, v, _ = raw[i]
            if v == '!':
                r, i = prim(i + 1); return (not r), i
            if v == '(':
                r, i = orx(i + 1)
                return r, i + 1  # ')'
            return (v in defines), i + 1
        def andx(i):
            r, i = prim(i)
            while i < len(raw) and raw[i][1] == '&&':
                r2, i = prim(i + 1); r = r and r2
            return r, i
        def orx(i):
            r, i = andx(i)
            while i < len(raw) and raw[i][1] == '||':
                r2, i = andx(i + 1); r = r or r2
            return r, i
        return orx(i)
    while i < len(raw):
        k, v, ln = raw[i]
        if k == 'pp':
            if v == '#if':
                c, i = cond(i + 1)
                stack.append((active, c, active and c))
                active = active and c
                continue
            if v == '#elseif':
                parent, taken, _ = stack.pop()
                c, i = cond(i + 1)
                now = parent and not taken and c
                stack.append((parent, taken or c, now)); active = now
                continue
            if v == '#else':
                parent, taken, _ = stack.pop()
                now = parent and not taken
                stack.append((parent, True, now)); active = now
                i += 1; continue
            if v == '#end':
                parent, _, _ = stack.pop(); active = parent
                i += 1; continue
            if v == '#error':
                i += 1; continue
        if active:
            if k == 'num':
                if v.startswith('0x'): val = int(v, 16)
                elif re.fullmatch(r'\d+', v): val = int(v)
                else: val = float(v.rstrip('.') if v.endswith('.') else v)
                out.append(('num', val, ln))
            elif k == 'str':
                out.append(('str', unescape(v[1:-1]), ln))
            elif k == 'id':
                out.append(('kw' if v in KEYWORDS else 'id', v, ln))
            else:
                out.append(('op', v, ln))
        i += 1
    out.append(('eof', None, line))
    return out

# précédences binaires de Haxe (plus grand = plus prioritaire)
BINOPS = {
    '%': 9, '*': 8, '/': 8, '+': 7, '-': 7, '<<': 6, '>>': 6, '>>>': 6,
    '|': 5, '&': 5, '^': 5,
    '==': 4, '!=': 4, '>': 4, '<': 4, '>=': 4, '<=': 4,
    '...': 3, '&&': 2, '||': 1,
}
ASSIGN = {'=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=', '>>>='}


class Parser:
    def __init__(self, toks, fname):
        self.t = toks; self.i = 0; self.fname = fname

    # --- utilitaires
    def peek(self, k=0): return self.t[self.i + k]
    def next(self):
        tok = self.t[self.i]; self.i += 1; return tok
    def is_(self, v, k=0):
        tok = self.t[self.i + k]
        return tok[1] == v and tok[0] in ('op', 'kw')
    def accept(self, v):
        if self.is_(v): self.i += 1; return True
        return False
    def err(self, msg):
        tok = self.peek()
        raise HxError('%s:%d: %s (trouvé %r)' % (self.fname, tok[2], msg, tok[1]))
    def expect(self, v):
        if not self.accept(v): self.err('attendu %r' % v)
    def ident(self):
        tok = self.next()
        if tok[0] == 'id' or (tok[0] == 'kw' and tok[1] in ('callback', 'dynamic')): return tok[1]
        self.i -= 1; self.err('identifiant attendu')
    def line(self): return self.peek()[2]

    # --- types (lus et ignorés ; on garde le chemin)
    def type_(self):
        t = self.type_prim()
        while self.accept('->'):
            self.type_prim()
        return t
    def type_prim(self):
        if self.accept('('):
            t = self.type_(); self.expect(')'); return t
        if self.accept('{'):
            # structure ou extension { >A, x : T, ?y : T }
            while not self.is_('}'):
                if self.accept('>'):
                    self.type_()
                elif self.accept('function'):
                    self.ident(); self.func_sig()
                else:
                    self.accept('?'); self.accept('var'); self.ident()
                    if self.accept('('):
                        # méthode dans un type structurel
                        while not self.is_(')'):
                            self.accept('?'); self.ident()
                            if self.accept(':'): self.type_()
                            self.accept(',')
                        self.expect(')')
                    self.expect(':'); self.type_()
                if not self.accept(','): self.accept(';')
            self.expect('}')
            return None
        path = [self.ident()]
        while self.is_('.'):
            self.next(); path.append(self.ident())
        if self.accept('<'):
            while True:
                self.type_()
                if not self.accept(','): break
            self.close_angle()
        return '.'.join(path)
    def close_angle(self):
        tok = self.peek()
        if tok[1] == '>': self.i += 1; return
        # >> ou >>> fermant plusieurs génériques
        if tok[1] in ('>>', '>>>', '>=', '>>='):
            rest = tok[1][1:]
            self.t[self.i] = ('op', rest, tok[2]); return
        self.err('> attendu')

    # --- fichier
    def file(self):
        pkg = []
        imports = []
        decls = []
        if self.accept('package'):
            if not self.is_(';'):
                pkg = [self.ident()]
                while self.accept('.'): pkg.append(self.ident())
            self.expect(';')
        while self.peek()[0] != 'eof':
            if self.accept('import'):
                p = [self.ident()]
                while self.accept('.'):
                    if self.accept('*'): p.append('*'); break
                    p.append(self.ident())
                self.expect(';'); imports.append(p); continue
            if self.accept(';'): continue
            decls.append(self.decl())
        return {'pkg': pkg, 'imports': imports, 'decls': decls}

    def decl(self):
        flags = set()
        while self.peek()[1] in ('private', 'extern', 'public') and self.peek()[0] == 'kw':
            flags.add(self.next()[1])
        if self.accept('class') or self.accept('interface'):
            is_iface = self.t[self.i - 1][1] == 'interface'
            name = self.ident()
            if self.accept('<'):
                while True:
                    self.ident()
                    if self.accept(':'):
                        if self.accept('('):
                            while not self.accept(')'): self.type_(); self.accept(',')
                        else: self.type_()
                    if not self.accept(','): break
                self.close_angle()
            sup = None; ifaces = []
            while True:
                if self.accept('extends'): sup = self.type_()
                elif self.accept('implements'): ifaces.append(self.type_())
                else: break
                self.accept(',')
            self.expect('{')
            fields = []
            while not self.accept('}'):
                fields.append(self.field())
            return ('class', name, sup, fields, 'extern' in flags or is_iface)
        if self.accept('enum'):
            name = self.ident()
            if self.accept('<'):
                while not self.accept('>'): self.next()
            self.expect('{')
            ctors = []
            while not self.accept('}'):
                c = self.ident(); args = []
                if self.accept('('):
                    while not self.accept(')'):
                        self.accept('?'); args.append(self.ident()); self.expect(':'); self.type_(); self.accept(',')
                self.expect(';')
                ctors.append((c, args))
            return ('enum', name, ctors)
        if self.accept('typedef'):
            name = self.ident()
            if self.accept('<'):
                while not self.accept('>'): self.next()
            self.expect('='); self.type_(); self.accept(';')
            return ('typedef', name)
        self.err('déclaration attendue')

    def field(self):
        mods = set()
        while self.peek()[0] == 'kw' and self.peek()[1] in ('static', 'public', 'private', 'override', 'inline', 'dynamic', 'f9dynamic'):
            mods.add(self.next()[1])
        if self.accept('var'):
            name = self.ident(); prop = None; init = None
            if self.accept('('):
                g = self.next()[1]; self.expect(',')
                s = self.next()[1]; self.expect(')')
                prop = (g, s)
            if self.accept(':'):
                self.type_()
                if self.is_('(') and self.is_(')', 1): self.i += 2  # « flash.MovieClip() » toléré
            if self.accept('='): init = self.expr()
            self.accept(';')  # ; parfois oublié dans les sources d'origine
            return ('var', name, 'static' in mods, init, prop)
        if self.accept('function'):
            name = 'new' if self.accept('new') else self.ident()
            if self.accept('<'):
                while not self.accept('>'): self.next()
            params, body = self.func_rest()
            return ('method', name, 'static' in mods, params, body)
        self.err('champ attendu')

    def func_sig(self):
        self.expect('(')
        while not self.accept(')'):
            self.accept('?'); self.ident()
            if self.accept(':'): self.type_()
            self.accept(',')
        if self.accept(':'): self.type_()

    def func_rest(self):
        self.expect('(')
        params = []
        while not self.accept(')'):
            opt = self.accept('?')
            n = self.ident(); dflt = None
            if self.accept(':'): self.type_()
            if self.accept('='): dflt = self.expr()
            params.append((n, opt, dflt))
            self.accept(',')
        if self.accept(':'): self.type_()
        body = None
        if self.is_('{') or not self.is_(';'):
            body = self.expr()
        else:
            self.expect(';')
        return params, body

    # --- instructions / expressions (en Haxe tout est expression)
    def block_items(self):
        items = []
        while not self.accept('}'):
            if self.accept(';'): continue
            e = self.stmt()
            items.append(e)
        return items

    def stmt(self):
        ln = self.line()
        if self.accept('var'):
            vs = []
            while True:
                n = self.ident(); init = None
                if self.accept(':'): self.type_()
                if self.accept('='): init = self.expr()
                vs.append((n, init))
                if not self.accept(','): break
            self.semi(optional=self.t[self.i - 1][1] == '}')
            return ('vars', vs, ln)
        e = self.expr()
        # le ; est optionnel après une expression terminée par un bloc
        self.semi(optional=self.t[self.i - 1][1] == '}')
        return e

    def semi(self, optional=False):
        if self.accept(';'): return
        if optional or self.is_('}'): return
        if self.peek()[0] == 'kw' and self.peek()[1] in ('case', 'default'): return
        self.err('; attendu')

    def expr(self):
        return self.assign()

    def assign(self):
        left = self.ternary()
        tok = self.peek()
        if tok[0] == 'op' and tok[1] in ASSIGN:
            self.next()
            right = self.assign()
            return ('assign', tok[1], left, right, tok[2])
        return left

    def ternary(self):
        c = self.binary(1)
        if self.accept('?'):
            a = self.assign(); self.expect(':'); b = self.assign()
            return ('if', c, a, b, True)
        return c

    def binary(self, minp):
        left = self.unary()
        while True:
            tok = self.peek()
            if tok[0] != 'op' or tok[1] not in BINOPS: return left
            p = BINOPS[tok[1]]
            if p < minp: return left
            self.next()
            right = self.binary(p + 1)
            left = ('bin', tok[1], left, right)

    def unary(self):
        tok = self.peek()
        if tok[0] == 'op' and tok[1] in ('!', '-', '~'):
            self.next()
            e = self.unary()
            if tok[1] == '-' and e[0] == 'const' and isinstance(e[1], (int, float)) and not isinstance(e[1], bool):
                return ('const', -e[1])
            return ('unop', tok[1], e)
        if tok[0] == 'op' and tok[1] in ('++', '--'):
            self.next()
            return ('incr', tok[1], self.unary(), True)
        return self.postfix(self.primary())

    def postfix(self, e):
        while True:
            if self.accept('.'):
                e = ('field', e, self.ident())
            elif self.accept('('):
                args = []
                while not self.accept(')'):
                    args.append(self.expr()); self.accept(',')
                e = ('call', e, args)
            elif self.accept('['):
                i = self.expr(); self.expect(']')
                e = ('index', e, i)
            elif self.is_('++') or self.is_('--'):
                op = self.next()[1]
                e = ('incr', op, e, False)
            else:
                return e

    def primary(self):
        tok = self.next()
        k, v, ln = tok
        if k == 'num': return ('const', v)
        if k == 'str': return ('const', v)
        if k == 'id': return ('ident', v, ln)
        if k == 'kw':
            if v == 'true': return ('const', True)
            if v == 'false': return ('const', False)
            if v == 'null': return ('null',)
            if v == 'this': return ('this',)
            if v == 'super': return ('super',)
            if v == 'callback': return ('ident', 'callback', ln)
            if v == 'dynamic': return ('ident', 'dynamic', ln)
            if v == 'new':
                t = self.type_()
                self.expect('(')
                args = []
                while not self.accept(')'):
                    args.append(self.expr()); self.accept(',')
                return ('new', t, args)
            if v == 'cast':
                if self.accept('('):
                    e = self.expr()
                    if self.accept(','): self.type_()
                    self.expect(')')
                    return e
                return self.unary()
            if v == 'untyped':
                return ('untyped', self.assign())
            if v == 'function':
                params, body = self.func_rest()
                return ('func', params, body)
            if v == 'if':
                self.expect('('); c = self.expr(); self.expect(')')
                a = self.stmt_expr()
                # « else » peut suivre un ; optionnel
                save = self.i
                self.accept(';')
                if self.accept('else'):
                    b = self.stmt_expr()
                else:
                    self.i = save; b = None
                return ('if', c, a, b, False)
            if v == 'while':
                self.expect('('); c = self.expr(); self.expect(')')
                return ('while', c, self.stmt_expr(), True)
            if v == 'do':
                body = self.stmt_expr(); self.accept(';')
                self.expect('while'); self.expect('('); c = self.expr(); self.expect(')')
                return ('while', c, body, False)
            if v == 'for':
                self.expect('('); n = self.ident(); self.expect('in'); it = self.expr(); self.expect(')')
                return ('for', n, it, self.stmt_expr())
            if v == 'return':
                if self.is_(';') or self.is_('}'): return ('return', None)
                return ('return', self.expr())
            if v == 'break': return ('break',)
            if v == 'continue': return ('continue',)
            if v == 'throw': return ('throw', self.expr())
            if v == 'try':
                body = self.stmt_expr(); catches = []
                while self.accept('catch'):
                    self.expect('('); n = self.ident()
                    if self.accept(':'): self.type_()
                    self.expect(')')
                    catches.append((n, self.stmt_expr()))
                return ('try', body, catches)
            if v == 'switch':
                self.expect('('); s = self.expr(); self.expect(')')
                self.expect('{')
                cases = []; dflt = None
                while not self.accept('}'):
                    if self.accept('default'):
                        self.expect(':'); dflt = self.case_body()
                    else:
                        self.expect('case')
                        pats = [self.expr()]
                        while self.accept(','): pats.append(self.expr())
                        self.expect(':')
                        cases.append((pats, self.case_body()))
                return ('switch', s, cases, dflt)
        if k == 'op':
            if v == '(':
                e = self.expr()
                if self.accept(':'): self.type_()  # (e : T)
                self.expect(')')
                return ('paren', e)
            if v == '[':
                items = []
                while not self.accept(']'):
                    items.append(self.expr()); self.accept(',')
                return ('array', items)
            if v == '{':
                # objet { a : 1 } ou bloc
                if self.is_('}'):
                    self.next(); return ('object', [])
                t0, t1 = self.peek(), self.peek(1)
                if (t0[0] in ('id', 'str') or t0[0] == 'kw') and t1[1] == ':' and t1[0] == 'op' and t0[1] not in ('case', 'default'):
                    fields = []
                    while not self.accept('}'):
                        n = self.next()[1]; self.expect(':'); fields.append((n, self.expr())); self.accept(',')
                    return ('object', fields)
                return ('block', self.block_items())
        self.i -= 1
        self.err('expression attendue')

    def stmt_expr(self):
        if self.accept('var'):
            self.i -= 1
            return self.stmt()
        return self.expr()

    def case_body(self):
        items = []
        while not (self.is_('case') or self.is_('default') or self.is_('}')):
            if self.accept(';'): continue
            items.append(self.stmt())
        return ('block', items)


def parse_file(path, defines=('flash', 'flash8')):
    with open(path, encoding='utf-8-sig', errors='replace') as f:
        src = f.read()
    toks = lex(src, path, set(defines))
    return Parser(toks, path).file()
