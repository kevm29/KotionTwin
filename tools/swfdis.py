#!/usr/bin/env python3
"""Désassembleur AVM1 minimal (Flash 5-8) : liste les DoAction / DoInitAction / boutons
d'un SWF, y compris dans les DefineSprite, avec le pool de constantes résolu.

Usage : python3 -I tools/swfdis.py fichier.swf [--strings] [--grep MOT]
  --strings  n'affiche que les pools de constantes (rapide pour repérer l'API attendue)
  --grep     n'affiche que les blocs dont le texte contient MOT
"""
import sys, zlib, struct
FULL = "--full" in sys.argv

OPS = {0x04:'NextFrame',0x05:'PrevFrame',0x06:'Play',0x07:'Stop',0x08:'ToggleQuality',0x09:'StopSounds',
0x0A:'Add',0x0B:'Subtract',0x0C:'Multiply',0x0D:'Divide',0x0E:'Equals',0x0F:'Less',0x10:'And',0x11:'Or',0x12:'Not',
0x13:'StringEquals',0x14:'StringLength',0x15:'StringExtract',0x17:'Pop',0x18:'ToInteger',0x1C:'GetVariable',
0x1D:'SetVariable',0x20:'SetTarget2',0x21:'StringAdd',0x22:'GetProperty',0x23:'SetProperty',0x24:'CloneSprite',
0x25:'RemoveSprite',0x26:'Trace',0x27:'StartDrag',0x28:'EndDrag',0x29:'StringLess',0x2A:'Throw',0x2B:'CastOp',
0x2C:'ImplementsOp',0x30:'RandomNumber',0x31:'MBStringLength',0x32:'CharToAscii',0x33:'AsciiToChar',0x34:'GetTime',
0x35:'MBStringExtract',0x36:'MBCharToAscii',0x37:'MBAsciiToChar',0x3A:'Delete',0x3B:'Delete2',0x3C:'DefineLocal',
0x3D:'CallFunction',0x3E:'Return',0x3F:'Modulo',0x40:'NewObject',0x41:'DefineLocal2',0x42:'InitArray',
0x43:'InitObject',0x44:'TypeOf',0x45:'TargetPath',0x46:'Enumerate',0x47:'Add2',0x48:'Less2',0x49:'Equals2',
0x4A:'ToNumber',0x4B:'ToString',0x4C:'PushDuplicate',0x4D:'StackSwap',0x4E:'GetMember',0x4F:'SetMember',
0x50:'Increment',0x51:'Decrement',0x52:'CallMethod',0x53:'NewMethod',0x54:'InstanceOf',0x55:'Enumerate2',
0x60:'BitAnd',0x61:'BitOr',0x62:'BitXor',0x63:'BitLShift',0x64:'BitRShift',0x65:'BitURShift',0x66:'StrictEquals',
0x67:'Greater',0x68:'StringGreater',0x69:'Extends',0x81:'GotoFrame',0x83:'GetURL',0x87:'StoreRegister',
0x88:'ConstantPool',0x8A:'WaitForFrame',0x8B:'SetTarget',0x8C:'GoToLabel',0x8D:'WaitForFrame2',
0x8E:'DefineFunction2',0x8F:'Try',0x94:'With',0x96:'Push',0x99:'Jump',0x9A:'GetURL2',0x9B:'DefineFunction',
0x9D:'If',0x9E:'Call',0x9F:'GotoFrame2'}

def cstr(b, p):
    e = b.index(0, p)
    return b[p:e].decode('latin-1'), e + 1

def dis(code, out, indent=''):
    pool = []
    p = 0
    while p < len(code):
        op = code[p]; start = p; p += 1
        if op == 0:
            out.append(f'{indent}{start:05x} End'); continue
        ln = 0
        if op >= 0x80:
            ln = struct.unpack('<H', code[p:p+2])[0]; p += 2
        a = code[p:p+ln]; p += ln
        name = OPS.get(op, f'op_{op:02x}')
        arg = ''
        try:
            if op == 0x88:
                n = struct.unpack('<H', a[:2])[0]; q = 2; pool = []
                for _ in range(n):
                    s, q = cstr(a, q); pool.append(s)
                arg = repr(pool) if FULL else repr(pool)[:4000]
            elif op == 0x96:
                q = 0; items = []
                while q < len(a):
                    t = a[q]; q += 1
                    if t == 0: s, q = cstr(a, q); items.append(repr(s))
                    elif t == 1: items.append(str(struct.unpack('<f', a[q:q+4])[0])); q += 4
                    elif t == 2: items.append('null')
                    elif t == 3: items.append('undefined')
                    elif t == 4: items.append(f'r{a[q]}'); q += 1
                    elif t == 5: items.append('true' if a[q] else 'false'); q += 1
                    elif t == 6: items.append(str(struct.unpack('<d', a[q+4:q+8] + a[q:q+4])[0])); q += 8
                    elif t == 7: items.append(str(struct.unpack('<i', a[q:q+4])[0])); q += 4
                    elif t == 8: i = a[q]; q += 1; items.append(repr(pool[i]) if i < len(pool) else f'c{i}')
                    elif t == 9: i = struct.unpack('<H', a[q:q+2])[0]; q += 2; items.append(repr(pool[i]) if i < len(pool) else f'c{i}')
                    else: items.append(f'?{t}'); break
                arg = ', '.join(items)
            elif op in (0x83,):
                s1, q = cstr(a, 0); s2, q = cstr(a, q); arg = f'{s1!r} {s2!r}'
            elif op in (0x8B, 0x8C):
                arg = repr(cstr(a, 0)[0])
            elif op in (0x99, 0x9D):
                off = struct.unpack('<h', a[:2])[0]; arg = f'-> {p+off:05x}'
            elif op == 0x87 or op == 0x81:
                arg = str(a[0] if op == 0x87 else struct.unpack('<H', a[:2])[0])
            elif op == 0x9B:
                fn, q = cstr(a, 0); n = struct.unpack('<H', a[q:q+2])[0]; q += 2; ps = []
                for _ in range(n): s, q = cstr(a, q); ps.append(s)
                size = struct.unpack('<H', a[q:q+2])[0]
                arg = f'{fn}({", ".join(ps)}) size={size}'
            elif op == 0x8E:
                fn, q = cstr(a, 0); n, rc, fl = struct.unpack('<HBH', a[q:q+5]); q += 5; ps = []
                for _ in range(n):
                    r = a[q]; q += 1; s, q = cstr(a, q); ps.append(f'{s}@r{r}' if r else s)
                size = struct.unpack('<H', a[q:q+2])[0]
                arg = f'{fn}({", ".join(ps)}) regs={rc} flags={fl:#x} size={size}'
            elif op == 0x9A:
                arg = str(a[0])
            elif op == 0x9F:
                arg = str(a[0])
            else:
                arg = a.hex() if a else ''
        except Exception as ex:
            arg = f'<err {ex}> ' + a.hex()
        out.append(f'{indent}{start:05x} {name} {arg}'.rstrip())
    return pool

def tags(body, p, end):
    while p + 2 <= end:
        th = struct.unpack('<H', body[p:p+2])[0]; p += 2
        code = th >> 6; ln = th & 63
        if ln == 63: ln = struct.unpack('<I', body[p:p+4])[0]; p += 4
        yield code, p, ln
        p += ln
        if code == 0: break

def load(path):
    b = open(path, 'rb').read()
    if b[:3] == b'CWS': body = zlib.decompress(b[8:])
    elif b[:3] == b'FWS': body = b[8:]
    else: raise SystemExit('format non géré : ' + b[:3].decode('latin-1'))
    nbits = body[0] >> 3; rl = (5 + 4 * nbits + 7) // 8
    return body, rl + 4

def walk(body, p, end, where, blocks):
    frame = 0
    for code, q, ln in tags(body, p, end):
        if code == 1: frame += 1
        elif code == 12: blocks.append((f'{where} frame {frame} DoAction', body[q:q+ln]))
        elif code == 59:
            sid = struct.unpack('<H', body[q:q+2])[0]
            blocks.append((f'{where} DoInitAction sprite {sid}', body[q+2:q+ln]))
        elif code == 39:
            sid = struct.unpack('<H', body[q:q+2])[0]
            walk(body, q + 4, q + ln, f'sprite {sid}', blocks)
        elif code == 56:
            n = struct.unpack('<H', body[q:q+2])[0]; r = q + 2; names = []
            for _ in range(n):
                cid = struct.unpack('<H', body[r:r+2])[0]; s, r = cstr(body, r + 2); names.append(f'{cid}={s}')
            blocks.append((f'{where} ExportAssets', ('\n'.join(names)).encode('latin-1')))
        elif code == 57:
            url, r = cstr(body, q); n = struct.unpack('<H', body[r:r+2])[0]
            blocks.append((f'{where} ImportAssets from {url}', b''))
        elif code == 34:  # DefineButton2 : actions des boutons
            sid = struct.unpack('<H', body[q:q+2])[0]
            off = struct.unpack('<H', body[q+3:q+5])[0]
            if off:
                r = q + 3 + off
                while r < q + ln:
                    nxt = struct.unpack('<H', body[r:r+2])[0]
                    stop = r + nxt if nxt else q + ln
                    blocks.append((f'{where} Button {sid} action', body[r+4:stop]))
                    if not nxt: break
                    r += nxt
        elif code == 26 or code == 70:  # PlaceObject2/3 avec clip actions
            flags = body[q]
            if flags & 0x80:
                blocks.append((f'{where} frame {frame} PlaceObject avec onClipEvent (non décodé)', b''))

def main():
    path = sys.argv[1]
    only_strings = '--strings' in sys.argv
    grep = sys.argv[sys.argv.index('--grep') + 1] if '--grep' in sys.argv else None
    body, p = load(path)
    blocks = []
    walk(body, p, len(body), 'root', blocks)
    for title, code in blocks:
        if 'Export' in title or 'Import' in title or not code:
            txt = code.decode('latin-1')
            if not grep or grep in txt or grep in title:
                print(f'=== {title}\n{txt}')
            continue
        out = []
        pool = dis(code, out, '  ')
        txt = '\n'.join(out)
        if grep and grep not in txt: continue
        print(f'=== {title} ({len(code)} octets)')
        if only_strings: print('  pool:', pool)
        else: print(txt)

if __name__ == '__main__':
    main()
