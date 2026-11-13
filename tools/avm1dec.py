#!/usr/bin/env python3
"""Décompilateur AVM1 rudimentaire : transforme la sortie de swfdis.py en pseudo-JS
(expressions reconstruites, sauts laissés en « goto »). Aide à la lecture, pas plus.

Usage : python3 -I tools/swfdis.py x.swf --full | python3 -I tools/avm1dec.py [debut fin]
"""
import sys, re, ast

BIN = {'Add2': '+', 'Add': '+', 'Subtract': '-', 'Multiply': '*', 'Divide': '/', 'Modulo': '%',
       'Less2': '<', 'Less': '<', 'Greater': '>', 'Equals2': '==', 'Equals': '==', 'StrictEquals': '===',
       'BitAnd': '&', 'BitOr': '|', 'BitXor': '^', 'BitLShift': '<<', 'BitRShift': '>>', 'BitURShift': '>>>',
       'StringAdd': '+', 'And': '&&', 'Or': '||', 'InstanceOf': 'instanceof'}

def parse_push(arg):
    out = []; i = 0
    toks = []
    # séparer sur les virgules hors chaînes
    cur = ''; q = None
    for ch in arg:
        if q:
            cur += ch
            if ch == q and not cur.endswith('\\' + q): q = None
        elif ch in '\'"':
            q = ch; cur += ch
        elif ch == ',':
            toks.append(cur.strip()); cur = ''
        else: cur += ch
    if cur.strip(): toks.append(cur.strip())
    for t in toks:
        if t[:1] in '\'"':
            try: out.append(repr(ast.literal_eval(t)))
            except Exception: out.append(t)
        else: out.append(t)
    return out

def member(o, k):
    if re.fullmatch(r"'[A-Za-z_$][A-Za-z0-9_$]*'", k): return f'{o}.{k[1:-1]}'
    return f'{o}[{k}]'

def run(lines, out):
    st = []; ind = '  '
    def pop():
        return st.pop() if st else '<?>'
    for ln in lines:
        m = re.match(r'\s*([0-9a-f]{5}) (\w+) ?(.*)$', ln)
        if not m:
            out.append(ln); continue
        off, op, arg = m.groups()
        def emit(s): out.append(f'{off}{ind}{s}')
        if op == 'Push': st.extend(parse_push(arg))
        elif op == 'Pop':
            v = pop(); emit(v + ';')
        elif op in BIN:
            b = pop(); a = pop(); st.append(f'({a} {BIN[op]} {b})')
        elif op == 'Not': st.append(f'!{pop()}')
        elif op in ('Increment', 'Decrement'): st.append(f'({pop()} {"+" if op=="Increment" else "-"} 1)')
        elif op in ('ToInteger', 'ToNumber', 'ToString', 'TypeOf'): st.append(f'{op}({pop()})')
        elif op == 'GetVariable':
            v = pop(); st.append(v[1:-1] if v[:1] in '\'"' else f'eval({v})')
        elif op == 'SetVariable':
            v = pop(); n = pop(); emit(f'{n[1:-1] if n[:1] in chr(39)+chr(34) else n} = {v};')
        elif op in ('DefineLocal',):
            v = pop(); n = pop(); emit(f'var {n[1:-1]} = {v};')
        elif op == 'DefineLocal2': emit(f'var {pop()[1:-1]};')
        elif op == 'GetMember':
            k = pop(); o = pop(); st.append(member(o, k))
        elif op == 'SetMember':
            v = pop(); k = pop(); o = pop(); emit(f'{member(o, k)} = {v};')
        elif op in ('Delete',):
            k = pop(); o = pop(); st.append(f'delete {member(o,k)}')
        elif op == 'StoreRegister':
            v = st[-1] if st else '<?>'
            emit(f'r{arg} = {v};');
            if st: st[-1] = f'r{arg}'
        elif op == 'PushDuplicate':
            v = st[-1] if st else '<?>'; st.append(v)
        elif op == 'StackSwap':
            if len(st) >= 2: st[-1], st[-2] = st[-2], st[-1]
        elif op == 'CallFunction':
            n = pop(); k = int(pop()) if st else 0
            args = [pop() for _ in range(k)]
            st.append(f'{n[1:-1] if n[:1] in chr(39)+chr(34) else n}({", ".join(args)})')
        elif op in ('CallMethod', 'NewMethod'):
            n = pop(); o = pop()
            try: k = int(pop())
            except ValueError: k = 0
            args = [pop() for _ in range(k)]
            f = o if n in ("''", 'undefined') else member(o, n)
            st.append(('new ' if op == 'NewMethod' else '') + f'{f}({", ".join(args)})')
        elif op == 'NewObject':
            n = pop()
            try: k = int(pop())
            except ValueError: k = 0
            args = [pop() for _ in range(k)]
            st.append(f'new {n[1:-1]}({", ".join(args)})')
        elif op == 'InitArray':
            try: k = int(pop())
            except ValueError: k = 0
            st.append('[' + ', '.join(pop() for _ in range(k)) + ']')
        elif op == 'InitObject':
            try: k = int(pop())
            except ValueError: k = 0
            items = []
            for _ in range(k):
                v = pop(); n = pop(); items.append(f'{n}: {v}')
            st.append('{' + ', '.join(items) + '}')
        elif op == 'Return': emit(f'return {pop()};')
        elif op == 'If': emit(f'if ({pop()}) goto {arg[3:]};')
        elif op == 'Jump': emit(f'goto {arg[3:]};')
        elif op in ('DefineFunction', 'DefineFunction2'):
            emit(f'--- function {arg}')
            st.append('function(){…}')
        elif op == 'Trace': emit(f'trace({pop()});')
        elif op == 'Throw': emit(f'throw {pop()};')
        elif op == 'Enumerate2': emit(f'for-in {pop()}'); st.append('<enum>')
        elif op == 'Extends':
            sup = pop(); sub = pop(); emit(f'{sub} extends {sup};')
        elif op == 'ConstantPool': emit('// pool')
        elif op == 'End': emit('end')
        else:
            emit(f'{op} {arg}  // pile={st[-3:]}')
        if op in ('Return', 'If', 'Jump') or op.startswith('Define'):
            pass

if __name__ == '__main__':
    lines = sys.stdin.read().splitlines()
    if len(sys.argv) == 3:
        a, b = int(sys.argv[1], 16), int(sys.argv[2], 16)
        lines = [l for l in lines if re.match(r'\s*([0-9a-f]{5}) ', l) and a <= int(l.split()[0], 16) <= b]
    out = []
    run(lines, out)
    print('\n'.join(out))
