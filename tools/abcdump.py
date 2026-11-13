# Minimal SWF/ABC disassembler (KotionTwin) (Python, no deps). Usage: abcdump.py file.swf [classFilterRegex]
import sys, zlib, struct, re
def swf_tags(path):
    b=open(path,'rb').read()
    body=zlib.decompress(b[8:]) if b[:3]==b'CWS' else b[8:]
    nbits=body[0]>>3; rl=(5+4*nbits+7)//8; pos=rl+4
    while pos+2<=len(body):
        th=struct.unpack('<H',body[pos:pos+2])[0]; code=th>>6; ln=th&63; pos+=2
        if ln==63: ln=struct.unpack('<I',body[pos:pos+4])[0]; pos+=4
        yield code, body[pos:pos+ln]; pos+=ln
        if code==0: break
class R:
    def __init__(s,d,p=0): s.d=d; s.p=p
    def u8(s): v=s.d[s.p]; s.p+=1; return v
    def u16(s): v=struct.unpack('<H',s.d[s.p:s.p+2])[0]; s.p+=2; return v
    def s24(s): v=int.from_bytes(s.d[s.p:s.p+3],'little',signed=True); s.p+=3; return v
    def u30(s):
        r=0; sh=0
        for i in range(5):
            b=s.u8(); r|=(b&0x7f)<<sh; sh+=7
            if not b&0x80: break
        return r
    def s32(s):
        r=0; sh=0
        for i in range(5):
            b=s.u8(); r|=(b&0x7f)<<sh; sh+=7
            if not b&0x80: break
        if sh<35 and r&(1<<(sh-1)): r-=1<<sh
        return r & 0xffffffff if False else (r if r<2**31 else r-2**32)
    def d64(s): v=struct.unpack('<d',s.d[s.p:s.p+8])[0]; s.p+=8; return v
class ABC:
    def __init__(s,data):
        r=R(data); r.u16(); r.u16()
        s.ints=[0]+[r.s32() for _ in range(max(0,r.u30()-1))]
        s.uints=[0]+[r.u30() for _ in range(max(0,r.u30()-1))]
        s.dbls=[0]+[r.d64() for _ in range(max(0,r.u30()-1))]
        n=r.u30(); s.strs=['']
        for _ in range(n-1):
            l=r.u30(); s.strs.append(r.d[r.p:r.p+l].decode('utf8','replace')); r.p+=l
        n=r.u30(); s.ns=[('','*')]
        for _ in range(n-1): k=r.u8(); s.ns.append((k,s.strs[r.u30()]))
        n=r.u30(); s.nss=[[]]
        for _ in range(n-1): s.nss.append([r.u30() for _ in range(r.u30())])
        n=r.u30(); s.mn=[None]
        for _ in range(n-1):
            k=r.u8()
            if k in (7,0xd): s.mn.append(('Q',r.u30(),r.u30()))
            elif k in (0xf,0x10): s.mn.append(('RTQ',r.u30()))
            elif k in (0x11,0x12): s.mn.append(('RTQL',))
            elif k in (9,0xe): s.mn.append(('M',r.u30(),r.u30()))
            elif k in (0x1b,0x1c): s.mn.append(('ML',r.u30()))
            elif k==0x1d: t=r.u30(); s.mn.append(('G',t,[r.u30() for _ in range(r.u30())]))
            else: raise Exception('mn kind %x'%k)
        n=r.u30(); s.methods=[]
        for _ in range(n):
            pc=r.u30(); rt=r.u30(); pt=[r.u30() for _ in range(pc)]; nm=r.u30(); fl=r.u8()
            if fl&8:
                for _ in range(r.u30()): r.u30(); r.u8()
            if fl&0x80: [r.u30() for _ in range(pc)]
            s.methods.append({'name':s.strs[nm],'params':pt,'ret':rt,'body':None})
        for _ in range(r.u30()):
            r.u30()
            for _ in range(r.u30()): r.u30(); r.u30()
        n=r.u30(); s.inst=[]
        for _ in range(n):
            name=r.u30(); sup=r.u30(); fl=r.u8()
            if fl&8: r.u30()
            ifs=[r.u30() for _ in range(r.u30())]; ii=r.u30()
            s.inst.append({'name':name,'super':sup,'iinit':ii,'traits':s.traits(r)})
        s.cls=[]
        for _ in range(n): ci=r.u30(); s.cls.append({'cinit':ci,'traits':s.traits(r)})
        s.scripts=[]
        for _ in range(r.u30()): si=r.u30(); s.scripts.append({'init':si,'traits':s.traits(r)})
        s.body_pos={}
        for _ in range(r.u30()):
            bstart=r.p
            m=r.u30(); ms=r.u30(); lr=r.u30(); isd=r.u30(); msd=r.u30(); cl=r.u30()
            code=r.d[r.p:r.p+cl]; r.p+=cl
            ex=[(r.u30(),r.u30(),r.u30(),r.u30(),r.u30()) for _ in range(r.u30())]
            tr=s.traits(r)
            s.methods[m]['body']=code
            s.body_pos[m]=(bstart,r.p)
    def traits(s,r):
        out=[]
        for _ in range(r.u30()):
            name=r.u30(); k=r.u8(); kind=k&0xf; t={'name':name,'kind':kind}
            if kind in (0,6): t['slot']=r.u30(); t['type']=r.u30(); vi=r.u30(); t['vi']=vi
            if kind in (0,6) and vi: t['vk']=r.u8()
            elif kind in (1,2,3): r.u30(); t['method']=r.u30()
            elif kind==4: r.u30(); t['cls']=r.u30()
            elif kind==5: r.u30(); t['method']=r.u30()
            if k&0x40:
                for _ in range(r.u30()): r.u30()
            out.append(t)
        return out
    def mname(s,i):
        if i==0 or i>=len(s.mn): return '*'
        m=s.mn[i]
        if m[0]=='Q':
            ns=s.ns[m[1]][1]; return (ns+'.' if ns else '')+s.strs[m[2]]
        if m[0]=='M': return s.strs[m[1]]
        if m[0]=='RTQ': return s.strs[m[1]]
        if m[0]=='G': return s.mname(m[1])+'<'+','.join(s.mname(x) for x in m[2])+'>'
        return '[rt]'
OPS={0x01:('bkpt',''),0x02:('nop',''),0x03:('throw',''),0x04:('getsuper','m'),0x05:('setsuper','m'),0x06:('dxns','s'),0x07:('dxnslate',''),0x08:('kill','u'),0x09:('label',''),0x0c:('ifnlt','o'),0x0d:('ifnle','o'),0x0e:('ifngt','o'),0x0f:('ifnge','o'),0x10:('jump','o'),0x11:('iftrue','o'),0x12:('iffalse','o'),0x13:('ifeq','o'),0x14:('ifne','o'),0x15:('iflt','o'),0x16:('ifle','o'),0x17:('ifgt','o'),0x18:('ifge','o'),0x19:('ifstricteq','o'),0x1a:('ifstrictne','o'),0x1b:('lookupswitch','L'),0x1c:('pushwith',''),0x1d:('popscope',''),0x1e:('nextname',''),0x1f:('hasnext',''),0x20:('pushnull',''),0x21:('pushundefined',''),0x23:('nextvalue',''),0x24:('pushbyte','b'),0x25:('pushshort','u'),0x26:('pushtrue',''),0x27:('pushfalse',''),0x28:('pushnan',''),0x29:('pop',''),0x2a:('dup',''),0x2b:('swap',''),0x2c:('pushstring','s'),0x2d:('pushint','i'),0x2e:('pushuint','u'),0x2f:('pushdouble','d'),0x30:('pushscope',''),0x31:('pushnamespace','u'),0x32:('hasnext2','uu'),0x40:('newfunction','f'),0x41:('call','u'),0x42:('construct','u'),0x43:('callmethod','uu'),0x44:('callstatic','uu'),0x45:('callsuper','mu'),0x46:('callproperty','mu'),0x47:('returnvoid',''),0x48:('returnvalue',''),0x49:('constructsuper','u'),0x4a:('constructprop','mu'),0x4c:('callproplex','mu'),0x4e:('callsupervoid','mu'),0x4f:('callpropvoid','mu'),0x53:('applytype','u'),0x55:('newobject','u'),0x56:('newarray','u'),0x57:('newactivation',''),0x58:('newclass','u'),0x59:('getdescendants','m'),0x5a:('newcatch','u'),0x5d:('findpropstrict','m'),0x5e:('findproperty','m'),0x5f:('finddef','m'),0x60:('getlex','m'),0x61:('setproperty','m'),0x62:('getlocal','u'),0x63:('setlocal','u'),0x64:('getglobalscope',''),0x65:('getscopeobject','B'),0x66:('getproperty','m'),0x68:('initproperty','m'),0x6a:('deleteproperty','m'),0x6c:('getslot','u'),0x6d:('setslot','u'),0x6e:('getglobalslot','u'),0x6f:('setglobalslot','u'),0x70:('convert_s',''),0x71:('esc_xelem',''),0x72:('esc_xattr',''),0x73:('convert_i',''),0x74:('convert_u',''),0x75:('convert_d',''),0x76:('convert_b',''),0x77:('convert_o',''),0x78:('checkfilter',''),0x80:('coerce','m'),0x81:('coerce_b',''),0x82:('coerce_a',''),0x83:('coerce_i',''),0x84:('coerce_d',''),0x85:('coerce_s',''),0x86:('astype','m'),0x87:('astypelate',''),0x88:('coerce_u',''),0x89:('coerce_o',''),0x90:('negate',''),0x91:('increment',''),0x92:('inclocal','u'),0x93:('decrement',''),0x94:('declocal','u'),0x95:('typeof',''),0x96:('not',''),0x97:('bitnot',''),0xa0:('add',''),0xa1:('subtract',''),0xa2:('multiply',''),0xa3:('divide',''),0xa4:('modulo',''),0xa5:('lshift',''),0xa6:('rshift',''),0xa7:('urshift',''),0xa8:('bitand',''),0xa9:('bitor',''),0xaa:('bitxor',''),0xab:('equals',''),0xac:('strictequals',''),0xad:('lessthan',''),0xae:('lessequals',''),0xaf:('greaterthan',''),0xb0:('greaterequals',''),0xb1:('instanceof',''),0xb2:('istype','m'),0xb3:('istypelate',''),0xb4:('in',''),0xc0:('increment_i',''),0xc1:('decrement_i',''),0xc2:('inclocal_i','u'),0xc3:('declocal_i','u'),0xc4:('negate_i',''),0xc5:('add_i',''),0xc6:('subtract_i',''),0xc7:('multiply_i',''),0xd0:('getlocal0',''),0xd1:('getlocal1',''),0xd2:('getlocal2',''),0xd3:('getlocal3',''),0xd4:('setlocal0',''),0xd5:('setlocal1',''),0xd6:('setlocal2',''),0xd7:('setlocal3',''),0xef:('debug','BuBu'),0xf0:('debugline','u'),0xf1:('debugfile','s'),0x35:('li8',''),0x36:('li16',''),0x37:('li32',''),0x38:('lf32',''),0x39:('lf64',''),0x3a:('si8',''),0x3b:('si16',''),0x3c:('si32',''),0x3d:('sf32',''),0x3e:('sf64',''),0x50:('sxi1',''),0x51:('sxi8',''),0x52:('sxi16','')}
def dis(a,code,ind='    '):
    r=R(code); out=[]
    while r.p<len(code):
        st=r.p; op=r.u8(); nm,args=OPS.get(op,('op%02x'%op,'')); vals=[]
        for c in args:
            if c=='m': vals.append(a.mname(r.u30()))
            elif c=='s': vals.append(repr(a.strs[r.u30()]))
            elif c=='i': vals.append(str(a.ints[r.u30()]))
            elif c=='d': vals.append(str(a.dbls[r.u30()]))
            elif c=='u': vals.append(str(r.u30()))
            elif c=='b': vals.append(str(int.from_bytes(bytes([r.u8()]),'little',signed=True)))
            elif c=='B': vals.append(str(r.u8()))
            elif c=='o': o=r.s24(); vals.append('->%d'%(r.p+o))
            elif c=='f': vals.append('m%d'%r.u30())
            elif c=='L':
                d=r.s24(); n=r.u30(); cs=[r.s24() for _ in range(n+1)]; vals.append('def->%d %s'%(st+d,[st+x for x in cs]))
        if nm in ('debugline','debugfile','debug'): continue
        out.append('%s%5d %s %s'%(ind,st,nm,' '.join(vals)))
    return '\n'.join(out)
if __name__=='__main__':
    flt=re.compile(sys.argv[2] if len(sys.argv)>2 else '.')
    showcode = '-q' not in sys.argv
    for code,data in swf_tags(sys.argv[1]):
        if code==76:
            r=R(data); n=r.u16(); syms=[]
            for _ in range(n):
                cid=r.u16(); e=data.index(b'\0',r.p); syms.append((cid,data[r.p:e].decode())); r.p=e+1
            print('# SymbolClass', [s for s in syms if s[0]==0] , len(syms))
        if code not in (72,82): continue
        if code==82:
            r=R(data); r.p=4; e=data.index(b'\0',4); data=data[e+1:]
        a=ABC(data)
        for i,ins in enumerate(a.inst):
            cn=a.mname(ins['name'])
            if not flt.search(cn): continue
            print('class %s extends %s'%(cn,a.mname(ins['super'])))
            for label,traits,init in (('static',a.cls[i]['traits'],a.cls[i]['cinit']),('inst',ins['traits'],ins['iinit'])):
                print('  [%s init]'%label)
                if showcode and a.methods[init]['body']: print(dis(a,a.methods[init]['body']))
                for t in traits:
                    tn=a.mname(t['name'])
                    if 'method' in t:
                        m=a.methods[t['method']]
                        print('  %s %s(%s):%s'%(label,tn,','.join(a.mname(p) for p in m['params']),a.mname(m['ret'])))
                        if showcode and m['body']: print(dis(a,m['body']))
                    else: print('  %s var %s:%s'%(label,tn,a.mname(t.get('type',0))))
