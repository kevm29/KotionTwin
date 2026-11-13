#!/usr/bin/env python3
"""Désassembleur AVM1 minimal (SWF Flash 5-8) : liste les DoAction/DoInitAction
avec résolution du constant pool. Usage : avm1dis.py fichier.swf [> sortie.txt]"""
import sys, zlib, struct

OPS = {0x04:'nextFrame',0x05:'prevFrame',0x06:'play',0x07:'stop',0x08:'toggleQuality',0x09:'stopSounds',
0x0A:'add',0x0B:'subtract',0x0C:'multiply',0x0D:'divide',0x0E:'equals',0x0F:'less',0x10:'and',0x11:'or',0x12:'not',
0x13:'stringEquals',0x14:'stringLength',0x15:'stringExtract',0x17:'pop',0x18:'toInteger',0x1C:'getVariable',0x1D:'setVariable',
0x20:'setTarget2',0x21:'stringAdd',0x22:'getProperty',0x23:'setProperty',0x24:'cloneSprite',0x25:'removeSprite',0x26:'trace',
0x27:'startDrag',0x28:'endDrag',0x29:'stringLess',0x2A:'throw',0x2B:'castOp',0x2C:'implementsOp',0x30:'randomNumber',
0x31:'mbStringLength',0x32:'charToAscii',0x33:'asciiToChar',0x34:'getTime',0x35:'mbStringExtract',0x36:'mbCharToAscii',
0x37:'mbAsciiToChar',0x3A:'delete',0x3B:'delete2',0x3C:'defineLocal',0x3D:'callFunction',0x3E:'return',0x3F:'modulo',
0x40:'newObject',0x41:'defineLocal2',0x42:'initArray',0x43:'initObject',0x44:'typeOf',0x45:'targetPath',0x46:'enumerate',
0x47:'add2',0x48:'less2',0x49:'equals2',0x4A:'toNumber',0x4B:'toString',0x4C:'pushDuplicate',0x4D:'stackSwap',
0x4E:'getMember',0x4F:'setMember',0x50:'increment',0x51:'decrement',0x52:'callMethod',0x53:'newMethod',0x54:'instanceOf',
0x55:'enumerate2',0x60:'bitAnd',0x61:'bitOr',0x62:'bitXor',0x63:'bitLShift',0x64:'bitRShift',0x65:'bitURShift',
0x66:'strictEquals',0x67:'greater',0x68:'stringGreater',0x69:'extends',
0x81:'gotoFrame',0x83:'getURL',0x87:'storeRegister',0x88:'constantPool',0x8A:'waitForFrame',0x8B:'setTarget',0x8C:'goToLabel',
0x8D:'waitForFrame2',0x8E:'defineFunction2',0x8F:'try',0x94:'with',0x96:'push',0x99:'jump',0x9A:'getURL2',0x9B:'defineFunction',
0x9D:'if',0x9E:'call',0x9F:'gotoFrame2'}

def cstr(b, i):
    j = b.index(b'\0', i); return b[i:j].decode('latin-1'), j + 1

def dis(b, pool, out, ind=0, start=0, end=None):
    i = start; end = len(b) if end is None else end
    while i < end:
        op = b[i]; pos = i; i += 1
        if op == 0: out.append('  '*ind + f'{pos:05x} end'); continue
        ln = 0
        if op >= 0x80: ln = struct.unpack_from('<H', b, i)[0]; i += 2
        d = b[i:i+ln]; nxt = i + ln; name = OPS.get(op, f'op{op:02x}'); arg = ''
        if op == 0x88:
            n = struct.unpack_from('<H', d)[0]; k = 2; pool[:] = []
            for _ in range(n): s, k = cstr(d, k); pool.append(s)
            arg = f'{n} entries'
        elif op == 0x96:
            k = 0; vals = []
            while k < ln:
                t = d[k]; k += 1
                if t == 0: s, k = cstr(d, k); vals.append(repr(s))
                elif t == 1: vals.append(repr(struct.unpack_from('<f', d, k)[0])); k += 4
                elif t == 2: vals.append('null')
                elif t == 3: vals.append('undefined')
                elif t == 4: vals.append(f'r{d[k]}'); k += 1
                elif t == 5: vals.append(str(bool(d[k]))); k += 1
                elif t == 6:
                    x = d[k:k+8]; vals.append(repr(struct.unpack('<d', x[4:]+x[:4])[0])); k += 8
                elif t == 7: vals.append(str(struct.unpack_from('<i', d, k)[0])); k += 4
                elif t == 8: c = d[k]; k += 1; vals.append(repr(pool[c]) if c < len(pool) else f'c{c}')
                elif t == 9: c = struct.unpack_from('<H', d, k)[0]; k += 2; vals.append(repr(pool[c]) if c < len(pool) else f'c{c}')
                else: vals.append('?'); break
            arg = ', '.join(vals)
        elif op in (0x9B, 0x8E):
            fn, k = cstr(d, 0); np_ = struct.unpack_from('<H', d, k)[0]; k += 2; params = []
            if op == 0x8E:
                regs = d[k]; flags = struct.unpack_from('<H', d, k+1)[0]; k += 3
                for _ in range(np_): r = d[k]; s, k = cstr(d, k+1); params.append(f'{s}:r{r}' if r else s)
            else:
                for _ in range(np_): s, k = cstr(d, k); params.append(s)
            size = struct.unpack_from('<H', d, k)[0]
            out.append('  '*ind + f'{pos:05x} function {fn}({", ".join(params)}) {{')
            dis(b, pool, out, ind+1, nxt, nxt+size)
            out.append('  '*ind + '}'); i = nxt + size; continue
        elif op in (0x99, 0x9D): arg = f'-> {nxt + struct.unpack_from("<h", d)[0]:05x}'
        elif op == 0x8C: arg = repr(cstr(d, 0)[0])
        elif op == 0x83: a, k = cstr(d, 0); arg = repr(a) + ' ' + repr(cstr(d, k)[0])
        elif op == 0x8B: arg = repr(cstr(d, 0)[0])
        elif op == 0x87: arg = f'r{d[0]}'
        elif op == 0x81: arg = str(struct.unpack_from('<H', d)[0])
        elif op == 0x94: size = struct.unpack_from('<H', d)[0]; out.append('  '*ind+f'{pos:05x} with {{'); dis(b,pool,out,ind+1,nxt,nxt+size); out.append('  '*ind+'}'); i=nxt+size; continue
        elif op == 0x8F:
            fl = d[0]; ts, cs, fs = struct.unpack_from('<HHH', d, 1)
            out.append('  '*ind+f'{pos:05x} try {{'); dis(b,pool,out,ind+1,nxt,nxt+ts)
            out.append('  '*ind+'} catch {'); dis(b,pool,out,ind+1,nxt+ts,nxt+ts+cs)
            out.append('  '*ind+'} finally {'); dis(b,pool,out,ind+1,nxt+ts+cs,nxt+ts+cs+fs); out.append('  '*ind+'}')
            i = nxt+ts+cs+fs; continue
        out.append('  '*ind + f'{pos:05x} {name} {arg}'.rstrip()); i = nxt

def tags(b, i, end):
    while i < end:
        h = struct.unpack_from('<H', b, i)[0]; i += 2; code, ln = h >> 6, h & 63
        if ln == 63: ln = struct.unpack_from('<I', b, i)[0]; i += 4
        yield code, b[i:i+ln]; i += ln

def main(path):
    raw = open(path, 'rb').read()
    b = raw[:8] + (zlib.decompress(raw[8:]) if raw[:3] == b'CWS' else raw[8:])
    nb = b[8] >> 3; off = 8 + (5 + 4*nb + 7)//8 + 4
    out = []; exports = {}
    def walk(data, start, where):
        frame = 0
        for code, t in tags(data, start, len(data)):
            if code == 1: frame += 1
            elif code == 56:
                n = struct.unpack_from('<H', t)[0]; k = 2
                for _ in range(n):
                    cid = struct.unpack_from('<H', t, k)[0]; s, k = cstr(t, k+2); exports[cid] = s
            elif code == 12:
                out.append(f'\n=== DoAction {where} frame {frame}'); dis(t, [], out)
            elif code == 59:
                cid = struct.unpack_from('<H', t)[0]
                out.append(f'\n=== DoInitAction sprite {cid} ({exports.get(cid, "?")})'); dis(t, [], out, start=2)
            elif code == 39:
                cid = struct.unpack_from('<H', t)[0]; walk(t, 4, f'sprite {cid}')
    walk(b, off, 'root')
    print('\n'.join(out))

if __name__ == '__main__':
    main(sys.argv[1])
