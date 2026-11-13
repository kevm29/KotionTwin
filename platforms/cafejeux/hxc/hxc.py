#!/usr/bin/env python3
"""hxc : compilateur d'un sous-ensemble de Haxe 2 vers du bytecode AVM1 (Flash 8).

Écrit pour KotionTwin parce que le compilateur Haxe 2.10 n'est pas disponible dans
l'environnement de construction. Il couvre ce qu'utilisent les jeux CaféJeux de Motion Twin :
classes, héritage, enums (avec filtrage dans switch), fermetures, propriétés, for/in,
try/catch, untyped… Le code produit est dynamique, comme celui de Haxe pour Flash 8 :
les classes vivent dans _global, les valeurs d'enum sont des tableaux ["Ctor", index, args…].

Usage : hxc.py -cp dir [-cp dir…] -main Main [-lib gfx.swf…] -o sortie.swf
               [--size 300x300] [--fps 40] [--bg FFFFFF] [Classe…]
"""
import os, sys, struct, zlib, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hxparse import parse_file, HxError

# ------------------------------------------------------------------ assembleur AVM1
class Asm:
    def __init__(self, pool):
        self.b = bytearray(); self.pool = pool
        self.fix = []  # (pos_offset_field, label)
        self.labels = {}
        self.nlabel = 0
    def op(self, code, data=b''):
        self.b.append(code)
        if code >= 0x80:
            self.b += struct.pack('<H', len(data)); self.b += data
    def label(self):
        self.nlabel += 1; return self.nlabel
    def mark(self, l): self.labels[l] = len(self.b)
    def jump(self, code, l):
        self.b.append(code); self.b += struct.pack('<H', 2)
        self.fix.append((len(self.b), l)); self.b += b'\0\0'
    def resolve(self):
        for pos, l in self.fix:
            off = self.labels[l] - (pos + 2)
            if not -32768 <= off <= 32767: raise HxError('saut trop long')
            self.b[pos:pos + 2] = struct.pack('<h', off)
        self.fix = []
    def push(self, *vals):
        data = bytearray()
        for v in vals:
            if v is None: data.append(2)
            elif v is Undef: data.append(3)
            elif isinstance(v, Reg): data += bytes([4, v.n])
            elif isinstance(v, bool): data += bytes([5, 1 if v else 0])
            elif isinstance(v, int) and -0x80000000 <= v <= 0x7fffffff: data.append(7); data += struct.pack('<i', v)
            elif isinstance(v, (int, float)):
                d = struct.pack('<d', float(v)); data.append(6); data += d[4:8] + d[0:4]
            elif isinstance(v, str):
                i = self.pool.index(v)
                if i is None: data.append(0); data += v.encode('utf-8') + b'\0'
                elif i < 256: data += bytes([8, i])
                else: data.append(9); data += struct.pack('<H', i)
            else: raise HxError('push %r' % (v,))
        self.op(0x96, bytes(data))

class UndefT: pass
Undef = UndefT()
class Reg:
    def __init__(self, n): self.n = n

class Pool:
    def __init__(self): self.items = []; self.idx = {}; self.size = 0; self.frozen = False
    def index(self, s):
        if s in self.idx: return self.idx[s]
        if self.frozen: return None
        n = len(s.encode('utf-8')) + 1
        if len(self.items) >= 65535 or self.size + n > 60000: return None
        self.idx[s] = len(self.items); self.items.append(s); self.size += n
        return self.idx[s]
    def action(self):
        data = struct.pack('<H', len(self.items)) + b''.join(s.encode('utf-8') + b'\0' for s in self.items)
        return bytes([0x88]) + struct.pack('<H', len(data)) + data

# ------------------------------------------------------------------ programme
NATIVE_TOP = {'MovieClip', 'Key', 'Mouse', 'TextField', 'SharedObject', 'Stage', 'Sound', 'Color',
              'TextFormat', 'Selection', 'System', 'LoadVars', 'XML', 'LocalConnection', 'Button',
              'MovieClipLoader', 'ContextMenu', 'ContextMenuItem', 'Camera', 'Video', 'NetStream'}
GLOBAL_NAMES = {'Math', 'Array', 'String', 'Object', 'Date', 'Number', 'Boolean', 'Function',
                'parseInt', 'parseFloat', 'isNaN', 'isFinite', 'setInterval', 'clearInterval',
                'escape', 'unescape', 'getTimer', 'Infinity', 'NaN', 'ASSetPropFlags'}

class TypeInfo:
    def __init__(self, kind, path, decl, module, fileinfo):
        self.kind = kind; self.path = path; self.decl = decl; self.module = module; self.file = fileinfo
        self.sup = None; self.inst = {}; self.stat = {}; self.ctors = {}

class Program:
    def __init__(self, cps):
        self.cps = cps; self.types = {}; self.files = []; self.loaded = set()
        self.ctor_index = {}  # nom de constructeur -> [TypeInfo]
        self.method_names = set(); self.var_names = set()
    def find_module(self, path):
        rel = path.replace('.', '/') + '.hx'
        for cp in self.cps:
            f = os.path.join(cp, rel)
            if os.path.exists(f): return f
        return None
    def load_module(self, path):
        if path in self.loaded: return True
        f = self.find_module(path)
        if not f: return False
        self.loaded.add(path)
        ast = parse_file(f)
        pkg = '.'.join(ast['pkg'])
        modname = path.split('.')[-1]
        fi = {'pkg': pkg, 'imports': ast['imports'], 'path': f, 'module': path, 'types': []}
        self.files.append(fi)
        for d in ast['decls']:
            if d[0] == 'typedef': continue
            name = d[1]
            full = (pkg + '.' if pkg else '') + name
            if d[0] == 'class' and d[4]:  # extern / interface
                continue
            ti = TypeInfo(d[0], full, d, path, fi)
            self.types[full] = ti; fi['types'].append(ti)
            if d[0] == 'enum':
                for i, (c, args) in enumerate(d[2]):
                    ti.ctors[c] = (i, len(args))
                    self.ctor_index.setdefault(c, []).append(ti)
        for imp in ast['imports']:
            if imp[-1] != '*': self.load_type_path('.'.join(imp))
        return True
    def load_type_path(self, path):
        if path in self.types: return True
        if self.load_module(path): return True
        parts = path.split('.')
        # type secondaire d'un module : a.b.Module.Type
        if len(parts) > 1 and self.load_module('.'.join(parts[:-1])): return True
        return False
    def load_all_in(self, cp):
        for root, dirs, files in os.walk(cp):
            for fn in files:
                if fn.endswith('.hx'):
                    rel = os.path.relpath(os.path.join(root, fn), cp)[:-3].replace(os.sep, '.')
                    try: self.load_module(rel)
                    except HxError: raise
    def finish(self):
        for ti in list(self.types.values()):
            if ti.kind != 'class': continue
            ti.inst = {}; ti.stat = {}
            for f in ti.decl[3]:
                if f[0] == 'var':
                    (ti.stat if f[2] else ti.inst)[f[1]] = ('var', f)
                    self.var_names.add(f[1])
                else:
                    (ti.stat if f[2] else ti.inst)[f[1]] = ('method', f)
                    if not f[2] and f[1] != 'new': self.method_names.add(f[1])
        for ti in list(self.types.values()):
            if ti.kind == 'class' and ti.decl[2]:
                ti.sup = self.resolve_type_name(ti.decl[2], ti.file)
    def resolve_type_name(self, name, fi):
        """Nom de type tel qu'écrit dans le fichier fi -> TypeInfo, ou chemin natif (str)."""
        if name in self.types and '.' in name: return self.types[name]
        # même module / même paquet
        for ti in fi['types']:
            if ti.path.split('.')[-1] == name: return ti
        for imp in fi['imports']:
            if imp[-1] == name:
                p = '.'.join(imp)
                if p in self.types: return self.types[p]
                if p.startswith('flash.'): return 'native:' + p
            if imp[-1] == '*':
                p = '.'.join(imp[:-1] + [name])
                if self.load_type_path(p) and p in self.types: return self.types[p]
            # types secondaires d'un module importé
            mod = '.'.join(imp)
            for ti in list(self.types.values()):
                if ti.module == mod and ti.path.split('.')[-1] == name: return ti
        p = (fi['pkg'] + '.' if fi['pkg'] else '') + name
        if p in self.types: return self.types[p]
        if self.load_type_path(p) and p in self.types: return self.types[p]
        if name in self.types: return self.types[name]
        if self.load_type_path(name) and name in self.types: return self.types[name]
        if name.startswith('flash.'): return 'native:' + name
        return None

# ------------------------------------------------------------------ génération de code
class Scope:
    def __init__(self, parent=None, func=None):
        self.parent = parent; self.names = {}; self.func = func

class FuncCtx:
    def __init__(self, cls, static, parent=None):
        self.cls = cls; self.static = static; self.parent = parent
        self.nreg = 1; self.maxreg = 1; self.free = []
        self.loops = []
        self.used = set() if parent is None else parent.used
    def reg(self):
        if self.free: return self.free.pop()
        r = Reg(self.nreg); self.nreg += 1; self.maxreg = max(self.maxreg, self.nreg)
        if self.nreg > 250: raise HxError('trop de registres')
        return r
    def release(self, r): self.free.append(r)


class Compiler:
    def __init__(self, prog):
        self.p = prog
        self.pool = Pool()
        self.uid = 0

    def err(self, msg): raise HxError(msg)

    # ---- chemins
    def push_path(self, a, parts):
        a.push('_global'); a.op(0x1C)
        for x in parts:
            a.push(x); a.op(0x4E)
    def type_parts(self, t):
        if isinstance(t, str):  # natif
            p = t[len('native:'):]
            parts = p.split('.')
            if p == 'flash.Lib': return ['flash', 'Lib']
            if parts[0] == 'flash' and len(parts) == 2: return [parts[1]]
            return parts
        return t.path.split('.')

    # ---- résolution d'identifiants
    def lookup_local(self, scope, name):
        s = scope
        while s:
            if name in s.names: return s.names[name]
            s = s.parent
        return None
    def declare(self, scope, ctx, name):
        base = name; n = base; i = 0
        while n in ctx.used or n in ('this', 'arguments', '_global', '_root', 'super'):
            i += 1; n = '%s$%d' % (base, i)
        ctx.used.add(n)
        scope.names[name] = n
        return n
    def member_of(self, ti, name, static):
        t = ti
        while isinstance(t, TypeInfo):
            d = t.stat if static else t.inst
            if name in d: return t, d[name]
            t = t.sup
        return None, None
    def has_native_super(self, ti):
        t = ti
        while isinstance(t, TypeInfo): t = t.sup
        return isinstance(t, str)

    def resolve(self, name, scope, ctx):
        if name in ('_root', '_global', '_level0', 'arguments'):
            return ('global', name)
        loc = self.lookup_local(scope, name)
        if loc: return ('local', loc)
        cls = ctx.cls
        if cls is not None:
            if not ctx.static or True:
                t, m = self.member_of(cls, name, False)
                if m and not ctx.static: return ('member', name, m[0])
            t, m = self.member_of(cls, name, True)
            if m: return ('static', t, name, m[0])
        fi = cls.file if cls else None
        if fi is not None:
            ti = self.p.resolve_type_name(name, fi)
            if ti is not None: return ('type', ti)
            # constructeurs d'enum : module courant, puis importés, puis n'importe lesquels
            cands = self.p.ctor_index.get(name, [])
            if cands:
                pref = [c for c in cands if c.file is fi] or [c for c in cands if any('.'.join(i) == c.module or '.'.join(i) == c.path for i in fi['imports'])] or cands
                return ('ctor', pref[0], name)
        if cls is not None and self.has_native_super(cls) and not ctx.static and name not in GLOBAL_NAMES:
            return ('member', name, 'native')
        return ('global', name)

    # ---- expressions
    def gen(self, a, e, scope, ctx, want):
        k = e[0]
        m = getattr(self, 'g_' + k)
        m(a, e, scope, ctx, want)

    def value(self, a, e, scope, ctx): self.gen(a, e, scope, ctx, True)
    def drop(self, a, want):
        if not want: a.op(0x17)

    def g_const(self, a, e, s, c, want):
        if want: a.push(e[1])
    def g_null(self, a, e, s, c, want):
        if want: a.push(None)
    def g_paren(self, a, e, s, c, want): self.gen(a, e[1], s, c, want)
    def g_untyped(self, a, e, s, c, want):
        c.untyped = getattr(c, 'untyped', 0) + 1
        try: self.gen(a, e[1], s, c, want)
        finally: c.untyped -= 1
    def push_this(self, a, s, c):
        a.push('$this'); a.op(0x1C)
    def g_this(self, a, e, s, c, want):
        if want: self.push_this(a, s, c)
    def g_super(self, a, e, s, c, want):
        self.err('super seul non géré')

    def g_ident(self, a, e, s, c, want):
        name = e[1]
        r = self.resolve(name, s, c)
        if r[0] == 'local':
            a.push(r[1]); a.op(0x1C)
        elif r[0] == 'member':
            self.push_this(a, s, c)
            if r[2] == 'method':
                a.op(0x17); self.bind(a, ('this',), name, s, c)
            else:
                a.push(name); a.op(0x4E)
        elif r[0] == 'static':
            self.push_path(a, r[1].path.split('.')); a.push(name); a.op(0x4E)
        elif r[0] == 'type':
            self.push_path(a, self.type_parts(r[1]))
        elif r[0] == 'ctor':
            self.push_path(a, r[1].path.split('.')); a.push(name); a.op(0x4E)
        else:
            if name == 'trace':
                self.push_path(a, ['haxe', 'Log']); a.push('trace'); a.op(0x4E)
            elif name in ('flash', 'mt', 'haxe') or name in self.p.packages:
                self.push_path(a, [name])
            elif name in GLOBAL_NAMES:
                self.push_path(a, [name])
            else:
                a.push(name); a.op(0x1C)
        self.drop(a, want)

    def g_field(self, a, e, s, c, want):
        obj, name = e[1], e[2]
        # chemin de type pkg.Type ?
        path = self.dotted(e)
        if path:
            r = self.resolve_dotted(path, s, c)
            if r is not None:
                kind, val = r
                if kind == 'type': self.push_path(a, self.type_parts(val))
                elif kind == 'static': self.push_path(a, val[0].path.split('.')); a.push(val[1]); a.op(0x4E)
                elif kind == 'ctor': self.push_path(a, val[0].path.split('.')); a.push(val[1]); a.op(0x4E)
                elif kind == 'native_static': self.push_path(a, self.type_parts(val[0])); a.push(val[1]); a.op(0x4E)
                self.drop(a, want); return
        if obj[0] == 'super':
            self.err('super.champ non géré')
        if name in self.p.method_names and name not in self.p.var_names and not getattr(c, 'untyped', 0):
            self.bind(a, obj, name, s, c)
        else:
            self.value(a, obj, s, c); a.push(name); a.op(0x4E)
        self.drop(a, want)

    def bind(self, a, obj, name, s, c):
        # $rt.bind(obj, name)
        a.push(name)
        self.value(a, obj, s, c)
        a.push(2); self.push_path(a, ['HxRt']); a.push('bind'); a.op(0x52)

    def dotted(self, e):
        parts = []
        while e[0] == 'field':
            parts.append(e[2]); e = e[1]
        if e[0] != 'ident': return None
        parts.append(e[1]); parts.reverse()
        return parts

    def resolve_dotted(self, parts, s, c):
        """a.b.c : si a est une variable locale/membre, ce n'est pas un chemin de type."""
        first = parts[0]
        r = self.resolve(first, s, c)
        if r[0] in ('local', 'member', 'static'): return None
        if r[0] == 'type' and len(parts) >= 2:
            return self.type_field(r[1], parts[1:], s, c)
        if r[0] == 'type' and len(parts) == 1: return ('type', r[1])
        # pkg.sub.Type(.field…)
        for n in range(len(parts), 0, -1):
            p = '.'.join(parts[:n])
            if p in self.p.types or self.p.load_type_path(p):
                if p in self.p.types:
                    ti = self.p.types[p]
                    if n == len(parts): return ('type', ti)
                    return self.type_field(ti, parts[n:], s, c)
            if p.startswith('flash.') and n >= 2 and parts[n - 1][:1].isupper():
                t = 'native:' + p
                if n == len(parts): return ('type', t)
                if n == len(parts) - 1: return ('native_static', (t, parts[n]))
                return None
        return None

    def type_field(self, ti, rest, s, c):
        if len(rest) != 1: return None
        name = rest[0]
        if isinstance(ti, TypeInfo):
            if ti.kind == 'enum' and name in ti.ctors: return ('ctor', (ti, name))
            if ti.kind == 'class':
                t, m = self.member_of(ti, name, True)
                if m: return ('static', (t, name))
            # sous-type du module : Module.Type
            mod = ti.module
            for t2 in list(self.p.types.values()):
                if t2.module == mod and t2.path.split('.')[-1] == name: return ('type', t2)
            return ('static', (ti, name))
        return ('native_static', (ti, name))

    def g_index(self, a, e, s, c, want):
        self.value(a, e[1], s, c); self.value(a, e[2], s, c); a.op(0x4E); self.drop(a, want)

    def g_array(self, a, e, s, c, want):
        for it in reversed(e[1]): self.value(a, it, s, c)
        a.push(len(e[1])); a.op(0x42); self.drop(a, want)

    def g_object(self, a, e, s, c, want):
        for n, v in e[1]:
            a.push(n); self.value(a, v, s, c)
        a.push(len(e[1])); a.op(0x43); self.drop(a, want)

    BIN = {'+': 0x47, '-': 0x0B, '*': 0x0C, '/': 0x0D, '%': 0x3F, '==': 0x49, '<': 0x48, '>': 0x67,
           '&': 0x60, '|': 0x61, '^': 0x62, '<<': 0x63, '>>': 0x64, '>>>': 0x65}

    def g_bin(self, a, e, s, c, want):
        op, l, r = e[1], e[2], e[3]
        if op in ('&&', '||'):
            self.value(a, l, s, c)
            a.op(0x4C)  # dup
            if op == '&&': a.op(0x12)
            end = a.label(); a.jump(0x9D, end)
            a.op(0x17); self.value(a, r, s, c)
            a.mark(end)
            self.drop(a, want); return
        if op == '...': self.err('... hors d\'un for')
        self.value(a, l, s, c); self.value(a, r, s, c)
        if op == '!=': a.op(0x49); a.op(0x12)
        elif op == '<=': a.op(0x67); a.op(0x12)
        elif op == '>=': a.op(0x48); a.op(0x12)
        else: a.op(self.BIN[op])
        self.drop(a, want)

    def g_unop(self, a, e, s, c, want):
        op = e[1]
        if op == '!': self.value(a, e[2], s, c); a.op(0x12)
        elif op == '-': a.push(0); self.value(a, e[2], s, c); a.op(0x0B)
        elif op == '~': self.value(a, e[2], s, c); a.push(-1); a.op(0x62)
        self.drop(a, want)

    # ---- affectations
    def lvalue(self, a, e, s, c):
        """Prépare une lvalue. Renvoie (get, set) : get() empile la valeur, set() consomme la valeur au sommet."""
        k = e[0]
        if k == 'paren': return self.lvalue(a, e[1], s, c)
        if k == 'ident':
            r = self.resolve(e[1], s, c)
            if r[0] == 'local':
                n = r[1]
                return (lambda: (a.push(n), a.op(0x1C)), lambda: (a.push(n), a.op(0x4D), a.op(0x1D)), None)
            if r[0] == 'member':
                obj = c.reg(); self.push_this(a, s, c); self._store(a, obj)
                return self._member_lv(a, obj, e[1], c)
            if r[0] == 'static':
                obj = c.reg(); self.push_path(a, r[1].path.split('.')); self._store(a, obj)
                return self._member_lv(a, obj, e[1], c)
            n = e[1]
            return (lambda: (a.push(n), a.op(0x1C)), lambda: (a.push(n), a.op(0x4D), a.op(0x1D)), None)
        if k == 'field':
            path = self.dotted(e)
            obj = c.reg()
            done = False
            if path:
                r = self.resolve_dotted(path[:-1], s, c) if len(path) > 1 else None
                if r is not None and r[0] == 'type':
                    self.push_path(a, self.type_parts(r[1])); done = True
            if not done: self.value(a, e[1], s, c)
            self._store(a, obj)
            return self._member_lv(a, obj, e[2], c)
        if k == 'index':
            obj = c.reg(); key = c.reg()
            self.value(a, e[1], s, c); self._store(a, obj)
            self.value(a, e[2], s, c); self._store(a, key)
            def get():
                a.push(obj, key); a.op(0x4E)
            def set_():
                tmp = c.reg(); self._store(a, tmp)
                a.push(obj, key, tmp); a.op(0x4F); c.release(tmp)
            return (get, set_, [obj, key])
        self.err('affectation invalide %r' % (k,))

    def _store(self, a, r):
        a.b += bytes([0x87]) + struct.pack('<H', 1) + bytes([r.n]); a.op(0x17)

    def _member_lv(self, a, obj, name, c):
        def get():
            a.push(obj, name); a.op(0x4E)
        def set_():
            tmp = c.reg(); self._store(a, tmp)
            a.push(obj, name, tmp); a.op(0x4F); c.release(tmp)
        return (get, set_, [obj])

    def g_assign(self, a, e, s, c, want):
        op, l, r = e[1], e[2], e[3]
        # cas simple : x = v sur une variable locale
        get, set_, regs = self.lvalue(a, l, s, c)
        if op == '=':
            self.value(a, r, s, c)
        else:
            get(); self.value(a, r, s, c)
            bop = op[:-1]
            a.op(self.BIN[bop])
        if want:
            tmp = c.reg(); a.b += bytes([0x87]) + struct.pack('<H', 1) + bytes([tmp.n])
            set_(); a.push(tmp); c.release(tmp)
        else:
            set_()
        for x in regs or []: c.release(x)

    def g_incr(self, a, e, s, c, want):
        op, target, prefix = e[1], e[2], e[3]
        get, set_, regs = self.lvalue(a, target, s, c)
        get()
        if want and not prefix: a.op(0x4C)  # garde l'ancienne valeur
        a.op(0x50 if op == '++' else 0x51)
        if want and prefix: a.op(0x4C)
        set_()
        for x in regs or []: c.release(x)

    # ---- appels
    def g_call(self, a, e, s, c, want):
        f, args = e[1], e[2]
        if f[0] == 'ident':
            name = f[1]
            if name == 'callback' and self.resolve(name, s, c)[0] == 'global':
                # callback(f, a, b) -> $rt.cb(f, [a, b])
                for x in reversed(args[1:]): self.value(a, x, s, c)
                a.push(len(args) - 1); a.op(0x42)
                self.value(a, args[0], s, c)
                a.push(2); self.push_path(a, ['HxRt']); a.push('cb'); a.op(0x52)
                self.drop(a, want); return
            if getattr(c, 'untyped', 0) or self.resolve(name, s, c)[0] == 'global':
                if name == '__unprotect__' or name == '__dollar__int' and False:
                    self.value(a, args[0], s, c); self.drop(a, want); return
                if name in ('__dollar__int', '__int__'):
                    self.value(a, args[0], s, c); a.op(0x18); self.drop(a, want); return
                if name == '__instanceof__':
                    self.value(a, args[0], s, c); self.value(a, args[1], s, c); a.op(0x54); self.drop(a, want); return
                if name == '__typeof__':
                    self.value(a, args[0], s, c); a.op(0x44); self.drop(a, want); return
                if name == '__delete__':
                    self.value(a, args[0], s, c); self.value(a, args[1], s, c); a.op(0x3A); self.drop(a, want); return
                if name == '__getTimer__':
                    a.op(0x34); self.drop(a, want); return
                if name == '__new__':
                    for x in reversed(args[1:]): self.value(a, x, s, c)
                    a.push(len(args) - 1); self.value(a, args[0], s, c); a.push(Undef); a.op(0x53)
                    self.drop(a, want); return
                if name == '__keys__':
                    # tableau des clés énumérables
                    arr = c.reg()
                    a.push(0); a.op(0x42); self._store(a, arr)
                    self.value(a, args[0], s, c); a.op(0x55)
                    loop = a.label(); end = a.label()
                    a.mark(loop)
                    a.b += bytes([0x87]) + struct.pack('<H', 1) + bytes([0])  # store r0
                    a.push(None); a.op(0x49); a.jump(0x9D, end)
                    a.push(Reg(0), 1, arr, 'push'); a.op(0x52); a.op(0x17)
                    a.jump(0x99, loop)
                    a.mark(end)
                    a.push(arr); c.release(arr); self.drop(a, want); return
                if name == '__this__':
                    a.push('this'); a.op(0x1C); self.drop(a, want); return
                if name == '__global__':
                    a.push('_global'); a.op(0x1C); self.drop(a, want); return
            r = self.resolve(name, s, c)
            if r[0] == 'local':
                self.push_args(a, args, s, c); a.push(r[1]); a.op(0x3D); self.drop(a, want); return
            if r[0] == 'member':
                self.push_args(a, args, s, c); self.push_this(a, s, c); a.push(name); a.op(0x52); self.drop(a, want); return
            if r[0] == 'static':
                self.push_args(a, args, s, c); self.push_path(a, r[1].path.split('.')); a.push(name); a.op(0x52); self.drop(a, want); return
            if r[0] == 'ctor':
                self.push_args(a, args, s, c); self.push_path(a, r[1].path.split('.')); a.push(name); a.op(0x52); self.drop(a, want); return
            if name == 'trace':
                self.push_args(a, args[:1], s, c); self.push_path(a, ['haxe', 'Log']); a.push('trace'); a.op(0x52); self.drop(a, want); return
            self.push_args(a, args, s, c); a.push(name); a.op(0x3D); self.drop(a, want); return
        if f[0] == 'super':
            # super(args) dans un constructeur
            sup = c.cls.sup
            if isinstance(sup, str):
                # $this = HxRt.superNative($this, Native, [args])
                a.push('$this')
                for x in reversed(args): self.value(a, x, s, c)
                a.push(len(args)); a.op(0x42)
                self.push_path(a, self.type_parts(sup)); self.push_this(a, s, c)
                a.push(3); self.push_path(a, ['HxRt']); a.push('superNative'); a.op(0x52)
                a.op(0x1D)
            else:
                self.push_args(a, args, s, c, extra_first=lambda: self.push_this(a, s, c))
                self.push_path(a, self.type_parts(sup)); a.push('call'); a.op(0x52); a.op(0x17)
                if self.has_native_super(sup):
                    a.push('$this'); self.push_path(a, ['HxRt', 'created']); a.op(0x1D)
            if want: a.push(Undef)
            return
        if f[0] == 'field':
            obj, name = f[1], f[2]
            if obj[0] == 'super':
                sup = c.cls.sup
                self.push_args(a, args, s, c, extra_first=lambda: self.push_this(a, s, c))
                self.push_path(a, self.type_parts(sup)); a.push('prototype'); a.op(0x4E); a.push(name); a.op(0x4E)
                a.push('call'); a.op(0x52); self.drop(a, want); return
            path = self.dotted(f)
            if path and len(path) > 1:
                r = self.resolve_dotted(path[:-1], s, c)
                if r is not None and r[0] == 'type':
                    self.push_args(a, args, s, c)
                    self.push_path(a, self.type_parts(r[1])); a.push(name); a.op(0x52)
                    self.drop(a, want); return
                if r is not None and r[0] in ('static', 'ctor', 'native_static'):
                    self.push_args(a, args, s, c)
                    self.g_field(a, f[1], s, c, True); a.push(name); a.op(0x52)
                    self.drop(a, want); return
            self.push_args(a, args, s, c)
            self.value(a, obj, s, c); a.push(name); a.op(0x52); self.drop(a, want); return
        # appel d'une expression quelconque
        self.push_args(a, args, s, c)
        self.value(a, f, s, c); a.push(Undef); a.op(0x52); self.drop(a, want)

    def push_args(self, a, args, s, c, extra_first=None):
        for x in reversed(args): self.value(a, x, s, c)
        if extra_first: extra_first()
        a.push(len(args) + (1 if extra_first else 0))

    def g_new(self, a, e, s, c, want):
        t, args = e[1], e[2]
        ti = self.p.resolve_type_name(t, c.cls.file) if c.cls else None
        if ti is None:
            r = self.resolve_dotted(t.split('.'), s, c)
            if r and r[0] == 'type': ti = r[1]
        if ti is None: ti = 'native:' + t if t.startswith('flash.') else None
        self.push_args(a, args, s, c)
        if ti is None:
            if t in ('Array', 'Date', 'String', 'Object'): parts = [t]
            else: parts = t.split('.')
        else:
            parts = self.type_parts(ti)
        if isinstance(ti, TypeInfo) and self.has_native_super(ti):
            # objet natif (BitmapData…) : fabrique Cls.__new(args)
            self.push_path(a, parts); a.push('__new'); a.op(0x52)
        else:
            self.push_path(a, parts[:-1]); a.push(parts[-1]); a.op(0x53)
        self.drop(a, want)

    def g_func(self, a, e, s, c, want):
        self.function(a, e[1], e[2], s, c.cls, c.static, c, name='')
        self.drop(a, want)

    # ---- structures de contrôle
    def g_block(self, a, e, s, c, want):
        inner = Scope(s)
        items = e[1]
        if not items:
            if want: a.push(Undef)
            return
        for i, it in enumerate(items):
            last = i == len(items) - 1
            self.gen(a, it, inner, c, want and last)

    def g_vars(self, a, e, s, c, want):
        for n, init in e[1]:
            if init is not None:
                # la variable n'est visible qu'après son initialisation
                self.value(a, init, s, c)
                avm = self.declare(s, c, n)
                a.push(avm); a.op(0x4D); a.op(0x3C)
            else:
                avm = self.declare(s, c, n)
                a.push(avm); a.op(0x41)
        if want: a.push(Undef)

    def g_if(self, a, e, s, c, want):
        cond, th, el = e[1], e[2], e[3]
        self.value(a, cond, s, c); a.op(0x12)
        lelse = a.label(); lend = a.label()
        a.jump(0x9D, lelse)
        self.gen(a, th, Scope(s), c, want)
        a.jump(0x99, lend)
        a.mark(lelse)
        if el is not None: self.gen(a, el, Scope(s), c, want)
        elif want: a.push(Undef)
        a.mark(lend)

    def g_while(self, a, e, s, c, want):
        cond, body, pre = e[1], e[2], e[3]
        top = a.label(); cont = a.label(); end = a.label()
        if pre:
            a.mark(top); a.mark(cont)
            self.value(a, cond, s, c); a.op(0x12); a.jump(0x9D, end)
            c.loops.append((end, cont)); self.gen(a, body, Scope(s), c, False); c.loops.pop()
            a.jump(0x99, top)
        else:
            a.mark(top)
            c.loops.append((end, cont)); self.gen(a, body, Scope(s), c, False); c.loops.pop()
            a.mark(cont)
            self.value(a, cond, s, c); a.jump(0x9D, top)
        a.mark(end)
        if want: a.push(Undef)

    def g_for(self, a, e, s, c, want):
        n, it, body = e[1], e[2], e[3]
        inner = Scope(s)
        top = a.label(); cont = a.label(); end = a.label()
        if it[0] == 'bin' and it[1] == '...':
            self.value(a, it[2], s, c)
            v = self.declare(inner, c, n)
            a.push(v); a.op(0x4D); a.op(0x3C)
            lim = c.reg(); self.value(a, it[3], s, c); self._store(a, lim)
            a.mark(top)
            a.push(v); a.op(0x1C); a.push(lim); a.op(0x48); a.op(0x12); a.jump(0x9D, end)
            c.loops.append((end, cont)); self.gen(a, body, Scope(inner), c, False); c.loops.pop()
            a.mark(cont)
            a.push(v); a.push(v); a.op(0x1C); a.op(0x50); a.op(0x1D)
            a.jump(0x99, top)
            a.mark(end); c.release(lim)
        else:
            itr = c.reg()
            self.value(a, it, s, c); a.push(1); self.push_path(a, ['HxRt']); a.push('iter'); a.op(0x52)
            self._store(a, itr)
            v = self.declare(inner, c, n)
            a.push(v); a.op(0x41)
            a.mark(top); a.mark(cont)
            a.push(0, itr, 'hasNext'); a.op(0x52); a.op(0x12); a.jump(0x9D, end)
            a.push(v, 0, itr, 'next'); a.op(0x52); a.op(0x1D)
            c.loops.append((end, cont)); self.gen(a, body, Scope(inner), c, False); c.loops.pop()
            a.jump(0x99, top)
            a.mark(end); c.release(itr)
        if want: a.push(Undef)

    def g_break(self, a, e, s, c, want): a.jump(0x99, c.loops[-1][0])
    def g_continue(self, a, e, s, c, want): a.jump(0x99, c.loops[-1][1])
    def g_return(self, a, e, s, c, want):
        if e[1] is None: a.push(Undef)
        else: self.value(a, e[1], s, c)
        a.op(0x3E)
    def g_throw(self, a, e, s, c, want):
        self.value(a, e[1], s, c); a.op(0x2A)

    def g_try(self, a, e, s, c, want):
        body, catches = e[1], e[2]
        if want: self.err('try comme valeur non géré')
        n, cbody = catches[0] if catches else ('e', ('block', []))
        inner = Scope(s); var = self.declare(inner, c, n)
        # ActionTry : corps puis bloc catch ; la variable d'exception est nommée
        sub = Asm(self.pool); sub.nlabel = a.nlabel + 1000
        c.loops_saved = c.loops;
        t = Asm(self.pool); self.gen(t, body, Scope(s), c, False); t.resolve()
        k = Asm(self.pool); self.gen(k, cbody, inner, c, False); k.resolve()
        tb = bytes(t.b); kb = bytes(k.b) + b''
        # saut par-dessus le catch à la fin du try
        tb += bytes([0x99]) + struct.pack('<Hh', 2, len(kb))
        data = bytes([0x01]) + struct.pack('<HHH', len(tb), len(kb), 0) + var.encode('utf-8') + b'\0'
        a.op(0x8F, data); a.b += tb + kb

    def g_switch(self, a, e, s, c, want):
        subj, cases, dflt = e[1], e[2], e[3]
        r = c.reg()
        self.value(a, subj, s, c); self._store(a, r)
        enum_mode = False
        for pats, _ in cases:
            for p in pats:
                if p[0] == 'call' and p[1][0] == 'ident' and self.resolve(p[1][1], s, c)[0] == 'ctor': enum_mode = True
                if p[0] == 'ident' and self.resolve(p[0 + 1], s, c)[0] == 'ctor': enum_mode = True
                if p[0] == 'call' and p[1][0] == 'field': enum_mode = True
        end = a.label()
        for pats, body in cases:
            nxt = a.label(); hit = a.label()
            binds = None
            for p in pats:
                if enum_mode:
                    cname = None; args = []
                    if p[0] == 'call':
                        cname = p[1][1] if p[1][0] == 'ident' else p[1][2]; args = p[2]
                    elif p[0] == 'ident': cname = p[1]
                    elif p[0] == 'field': cname = p[2]
                    a.push(r, 0); a.op(0x4E); a.push(cname); a.op(0x49)
                    a.jump(0x9D, hit)
                    if args: binds = args
                else:
                    a.push(r); self.value(a, p, s, c); a.op(0x49); a.jump(0x9D, hit)
            a.jump(0x99, nxt)
            a.mark(hit)
            inner = Scope(s)
            if binds:
                for i, b in enumerate(binds):
                    if b[0] == 'ident' and b[1] != '_':
                        a.push(r, i + 2); a.op(0x4E)
                        v = self.declare(inner, c, b[1]); a.push(v); a.op(0x4D); a.op(0x3C)
            self.gen(a, body, inner, c, want)
            a.jump(0x99, end)
            a.mark(nxt)
        if dflt is not None: self.gen(a, dflt, Scope(s), c, want)
        elif want: a.push(Undef)
        a.mark(end)
        c.release(r)

    # ---- fonctions
    def function(self, a, params, body, scope, cls, static, parent_ctx, name='', is_method=False, prologue=None):
        ctx = FuncCtx(cls, static, parent_ctx)
        ctx.used = set(parent_ctx.used) if parent_ctx else set()
        fs = Scope(scope)
        pnames = []
        for (n, opt, dflt) in params:
            pnames.append(self.declare(fs, ctx, n))
        b = Asm(self.pool)
        if is_method:
            b.push('$this', 'this'); b.op(0x1C); b.op(0x3C)
        for (n, opt, dflt), pn in zip(params, pnames):
            if dflt is not None:
                l = b.label()
                b.push(pn); b.op(0x1C); b.push(None); b.op(0x49); b.op(0x12); b.jump(0x9D, l)
                b.push(pn); self.value(b, dflt, fs, ctx); b.op(0x1D)
                b.mark(l)
        if prologue: prologue(b, fs, ctx)
        if body is not None:
            self.gen(b, body, fs, ctx, False)
        b.resolve()
        code = bytes(b.b)
        if len(code) > 65535: raise HxError('fonction trop grande')
        data = name.encode() + b'\0' + struct.pack('<HB', len(pnames), ctx.maxreg + 1)
        data += struct.pack('<H', 0)  # drapeaux : this/arguments/super disponibles par nom
        for pn in pnames: data += b'\0' + pn.encode('utf-8') + b'\0'
        data += struct.pack('<H', len(code))
        a.op(0x8E, data); a.b += code

    # ---- classes / programme
    def compile(self, main):
        a = Asm(self.pool)
        root = Scope()
        top = FuncCtx(None, True)
        # paquets
        made = set()
        def ensure_pkg(parts):
            for i in range(1, len(parts) + 1):
                p = tuple(parts[:i])
                if p in made: continue
                made.add(p)
                # if (_global.a.b == undefined) _global.a.b = {}
                l = a.label()
                self.push_path(a, list(p)); a.push(Undef); a.op(0x49); a.op(0x12); a.jump(0x9D, l)
                self.push_path(a, list(p[:-1])); a.push(p[-1]); a.push(0); a.op(0x43); a.op(0x4F)
                a.mark(l)
        types = [t for f in self.p.files for t in f['types']]
        self.p.packages = set(t.path.split('.')[0] for t in types if '.' in t.path)
        # ordre : super-classes avant les classes filles
        order = []; seen = set()
        def visit(t):
            if t.path in seen: return
            seen.add(t.path)
            if isinstance(t.sup, TypeInfo): visit(t.sup)
            order.append(t)
        for t in types: visit(t)
        for t in order:
            parts = t.path.split('.')
            ensure_pkg(parts[:-1])
            if t.kind == 'enum': self.enum_def(a, t)
            else: self.class_def(a, t, root)
        # initialisations statiques
        for t in order:
            if t.kind != 'class': continue
            for f in t.decl[3]:
                if f[0] == 'var' and f[2] and f[3] is not None:
                    self.push_path(a, t.path.split('.'))
                    a.push(f[1])
                    ctx = FuncCtx(t, True)
                    self.function(a, [], ('block', [('return', f[3])]), root, t, True, None)
                    a.push(0); a.op(0x4D); a.push(Undef); a.op(0x52)  # appel immédiat
                    a.op(0x4F)
        # main
        self.push_args(a, [], root, top)
        self.push_path(a, main.split('.')); a.push('main'); a.op(0x52); a.op(0x17)
        a.resolve()
        return self.pool.action()[0:0] + bytes(a.b)

    def enum_def(self, a, t):
        parts = t.path.split('.')
        self.push_path(a, parts[:-1]); a.push(parts[-1])
        a.push('__ename__', t.path, '__constructs__')
        for c, _ in reversed(t.decl[2]): a.push(c)
        a.push(len(t.decl[2])); a.op(0x42)
        a.push(2); a.op(0x43); a.op(0x4F)
        for i, (c, args) in enumerate(t.decl[2]):
            self.push_path(a, parts); a.push(c)
            if not args:
                a.push(i, c, 2); a.op(0x42)
                a.op(0x4F)
                # .__enum__
                self.push_path(a, parts); a.push(c); a.op(0x4E); a.push('__enum__'); self.push_path(a, parts); a.op(0x4F)
            else:
                params = [(x, False, None) for x in args]
                body_args = [('ident', x, 0) for x in args]
                # function(a,b){ var r = ["C", i, a, b]; r.__enum__ = E; return r; }
                cl = t
                def pro(b, fs, ctx, c=c, i=i, args=args, parts=parts):
                    for x in reversed(args):
                        b.push(fs.names[x]); b.op(0x1C)
                    b.push(i, c, len(args) + 2); b.op(0x42)
                    b.op(0x4C); b.push('__enum__'); self.push_path(b, parts); b.op(0x4F)
                    b.op(0x3E)
                self.function(a, params, None, Scope(), None, True, None, prologue=pro)
                a.op(0x4F)

    def class_def(self, a, t, root):
        parts = t.path.split('.')
        fields = t.decl[3]
        ctor = next((f for f in fields if f[0] == 'method' and f[1] == 'new'), None)
        native = self.has_native_super(t)
        self.push_path(a, parts[:-1]); a.push(parts[-1])
        if ctor:
            self.function(a, ctor[3], ctor[4], root, t, False, None, is_method=True)
        elif isinstance(t.sup, TypeInfo):
            sup_parts = self.type_parts(t.sup)
            def pro(b, fs, ctx):
                b.push('arguments'); b.op(0x1C); b.push('this'); b.op(0x1C); b.push(2)
                self.push_path(b, sup_parts); b.push('apply'); b.op(0x52); b.op(0x17)
            self.function(a, [], None, root, t, False, None, prologue=pro)
        else:
            self.function(a, [], None, root, t, False, None)
        a.op(0x4F)
        # héritage : Cls.prototype.__proto__ = Sup.prototype
        if t.sup is not None:
            self.push_path(a, parts); a.push('prototype'); a.op(0x4E); a.push('__proto__')
            self.push_path(a, self.type_parts(t.sup)); a.push('prototype'); a.op(0x4E); a.op(0x4F)
        # nom de classe
        self.push_path(a, parts); a.push('__name__', t.path); a.op(0x4F)
        self.push_path(a, parts); a.push('prototype'); a.op(0x4E); a.push('__class__'); self.push_path(a, parts); a.op(0x4F)
        for f in fields:
            if f[0] == 'method' and f[1] != 'new' and f[4] is not None:
                if f[2]:
                    self.push_path(a, parts); a.push(f[1])
                    self.function(a, f[3], f[4], root, t, True, None)
                else:
                    self.push_path(a, parts); a.push('prototype'); a.op(0x4E); a.push(f[1])
                    self.function(a, f[3], f[4], root, t, False, None, is_method=True)
                a.op(0x4F)
        # propriétés (get/set) -> addProperty
        for f in fields:
            if f[0] == 'var' and f[4]:
                g, st = f[4]
                if g not in ('default', 'null', 'never', 'dynamic') or st not in ('default', 'null', 'never', 'dynamic'):
                    tgt = (lambda: self.push_path(a, parts)) if f[2] else (lambda: (self.push_path(a, parts), a.push('prototype'), a.op(0x4E)))
                    # setter puis getter puis nom (ordre inverse des arguments)
                    for acc in (st, g):
                        if acc in ('default', 'null', 'never', 'dynamic'): a.push(None)
                        else: tgt(); a.push(acc); a.op(0x4E)
                    a.push(f[1], 3); tgt(); a.push('addProperty'); a.op(0x52); a.op(0x17)
        if native:
            # fabrique : crée l'objet natif puis applique le constructeur de la classe
            nat = t
            while isinstance(nat, TypeInfo): nat = nat.sup
            nparts = self.type_parts(nat)
            self.push_path(a, parts); a.push('__new')
            def pro(b, fs, ctx, nparts=nparts, parts=parts):
                # var o = $rt.newNative(Native, Cls, arguments)
                b.push('arguments'); b.op(0x1C)
                self.push_path(b, parts); self.push_path(b, nparts)
                b.push(3); self.push_path(b, ['HxRt']); b.push('newNative'); b.op(0x52); b.op(0x3E)
            self.function(a, [], None, root, t, True, None, prologue=pro)
            a.op(0x4F)


# ------------------------------------------------------------------ SWF
def tag(code, data):
    if len(data) < 63 and code not in (21, 35, 36, 20):
        return struct.pack('<H', (code << 6) | len(data)) + data
    return struct.pack('<HI', (code << 6) | 63, len(data)) + data

def rect(w, h):
    vals = [0, w * 20, 0, h * 20]
    nb = max(v.bit_length() for v in vals) + 1
    bits = format(nb, '05b') + ''.join(format(v, '0%db' % nb) for v in vals)
    bits += '0' * (-len(bits) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))

def write_swf(path, code_tags, w, h, fps, bg, libs):
    body = rect(w, h) + struct.pack('<HH', int(fps * 256), 1)
    tags = tag(9, bytes.fromhex(bg))
    tags += code_tags
    tags += tag(1, b'') + tag(0, b'')
    raw = b'FWS' + bytes([8]) + struct.pack('<I', 8 + len(body) + len(tags)) + body + tags
    tmp = path + '.base.swf'
    with open(tmp, 'wb') as f: f.write(raw)
    if libs:
        import subprocess
        here = os.path.dirname(os.path.abspath(__file__))
        subprocess.check_call([sys.executable, os.path.join(here, 'swfmerge.py'), tmp, path] + libs)
        os.remove(tmp)
    else:
        os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-cp', action='append', default=[])
    ap.add_argument('-main', default='Main')
    ap.add_argument('-lib', action='append', default=[])
    ap.add_argument('-o', required=True)
    ap.add_argument('--size', default='300x300')
    ap.add_argument('--fps', type=float, default=40)
    ap.add_argument('--bg', default='FFFFFF')
    ap.add_argument('classes', nargs='*')
    o = ap.parse_args()
    prog = Program(o.cp)
    prog.packages = set()
    for c in ['HxRt', 'Std', 'haxe.Log', 'Reflect', 'Type'] + [o.main] + o.classes:
        if not prog.load_type_path(c): raise HxError('classe introuvable : ' + c)
    # charge les modules référencés au fil de la compilation
    # des modules sont chargés au fil de la compilation : on recommence tant qu'il en arrive
    n = -1
    while True:
        n = len(prog.files)
        prog.finish()
        comp = Compiler(prog)
        try:
            code = comp.compile(o.main)
        except (AttributeError, KeyError, TypeError):
            if len(prog.files) != n: continue
            raise
        if len(prog.files) == n: break
    data = comp.pool.action() + code + b'\0'
    w, h = map(int, o.size.split('x'))
    write_swf(o.o, tag(12, data), w, h, o.fps, o.bg, o.lib)
    print('%s : %d octets de code, %d types' % (o.o, len(data), len(prog.types)))

if __name__ == '__main__':
    try: main()
    except HxError as e:
        print('erreur :', e); sys.exit(1)
