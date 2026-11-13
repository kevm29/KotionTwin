import sys, zlib, struct
def load(p):
    b=open(p,'rb').read()
    if b[:3]==b'CWS': body=zlib.decompress(b[8:])
    else: body=b[8:]
    nb=body[0]>>3; rl=(5+4*nb+7)//8
    return body, rl+4
def tags(body,pos,end):
    while pos+2<=end:
        th=struct.unpack('<H',body[pos:pos+2])[0]; code=th>>6; ln=th&63; pos+=2
        if ln==63: ln=struct.unpack('<I',body[pos:pos+4])[0]; pos+=4
        yield code,pos,ln
        pos+=ln
        if code==0: break
def cstr(b,i):
    j=b.index(0,i); return b[i:j].decode('latin1'),j+1
NAMES={0x04:'nextFrame',0x07:'stop',0x0a:'add',0x0b:'sub',0x0c:'mul',0x0d:'div',0x12:'not',0x17:'pop',0x1c:'getVariable',0x1d:'setVariable',0x26:'trace',0x3c:'defineLocal',0x3d:'callFunction',0x3e:'return',0x40:'newObject',0x41:'defineLocal2',0x42:'initArray',0x43:'initObject',0x44:'typeof',0x47:'add2',0x48:'less2',0x49:'equals2',0x4c:'pushDup',0x4e:'getMember',0x4f:'setMember',0x52:'callMethod',0x53:'newMethod',0x54:'instanceOf',0x60:'bitAnd',0x66:'strictEq',0x67:'greater',0x69:'extends',0x2b:'castOp',0x2c:'implements'}
def actions(b,pos,end,out,ind='',pool=None):
    if pool is None: pool=[]
    while pos<end:
        op=b[pos]; pos+=1
        if op==0: break
        ln=0
        if op>=0x80: ln=struct.unpack('<H',b[pos:pos+2])[0]; pos+=2
        d=b[pos:pos+ln]
        if op==0x88:
            n=struct.unpack('<H',d[:2])[0]; i=2; pool.clear()
            for _ in range(n): s,i=cstr(d,i); pool.append(s)
            out.append(ind+'constantPool '+repr(pool))
        elif op==0x96:
            i=0; vals=[]
            while i<ln:
                t=d[i]; i+=1
                if t==0: s,i=cstr(d,i); vals.append(repr(s))
                elif t==1: vals.append(str(struct.unpack('<f',d[i:i+4])[0])); i+=4
                elif t==2: vals.append('null')
                elif t==3: vals.append('undef')
                elif t==4: vals.append('r%d'%d[i]); i+=1
                elif t==5: vals.append(str(bool(d[i]))); i+=1
                elif t==6: vals.append(str(struct.unpack('<d',d[i+4:i+8]+d[i:i+4])[0])); i+=8
                elif t==7: vals.append(str(struct.unpack('<i',d[i:i+4])[0])); i+=4
                elif t==8: vals.append('c:'+repr(pool[d[i]] if d[i]<len(pool) else d[i])); i+=1
                elif t==9: k=struct.unpack('<H',d[i:i+2])[0]; vals.append('c:'+repr(pool[k] if k<len(pool) else k)); i+=2
            out.append(ind+'push '+', '.join(vals))
        elif op in (0x9b,0x8e):
            nm,i=cstr(d,0)
            if op==0x9b:
                n=struct.unpack('<H',d[i:i+2])[0]; i+=2; ps=[]
                for _ in range(n): s,i=cstr(d,i); ps.append(s)
                sz=struct.unpack('<H',d[i:i+2])[0]
            else:
                n=struct.unpack('<H',d[i:i+2])[0]; i+=2; i+=1; i+=2; ps=[]
                for _ in range(n): r=d[i]; i+=1; s,i=cstr(d,i); ps.append('r%d:%s'%(r,s))
                sz=struct.unpack('<H',d[i:i+2])[0]
            out.append(ind+'function %s(%s) {'%(nm,','.join(ps)))
            pos+=ln
            # inner shares pool
            sub=[]; actions(b,pos,pos+sz,sub,ind+'  ',pool); out+=sub
            out.append(ind+'}')
            pos+=sz; continue
        elif op==0x83:
            u,i=cstr(d,0); t,i=cstr(d,i); out.append(ind+'getURL %r %r'%(u,t))
        elif op==0x99: out.append(ind+'jump %d'%struct.unpack('<h',d)[0])
        elif op==0x9d: out.append(ind+'if %d'%struct.unpack('<h',d)[0])
        elif op==0x87: out.append(ind+'storeRegister %d'%d[0])
        else: out.append(ind+NAMES.get(op,'op%02x'%op)+(' '+d.hex() if ln else ''))
        pos+=ln
def actions_inner(b,pos,end,out,ind,pool):
    # same as actions but with given pool: hack by injecting
    global _p
    actions(b,pos,end,out,ind)
def walk(body,pos,end,out,depth=0):
    for code,p,ln in tags(body,pos,end):
        if code==39:
            sid=struct.unpack('<H',body[p:p+2])[0]
            walk(body,p+4,p+ln,out,depth+1)
        elif code==12:
            out.append('== DoAction depth%d'%depth); actions(body,p,p+ln,out)
        elif code==59:
            sid=struct.unpack('<H',body[p:p+2])[0]
            out.append('== DoInitAction sprite %d'%sid); actions(body,p+2,p+ln,out)
        elif code==56:
            n=struct.unpack('<H',body[p:p+2])[0]; i=p+2; ex=[]
            for _ in range(n):
                cid=struct.unpack('<H',body[i:i+2])[0]; s,i=cstr(body,i+2); ex.append('%d=%s'%(cid,s))
            out.append('== Export '+' '.join(ex))
        elif code==26 or code==70:
            pass
body,pos=load(sys.argv[1]); out=[]; walk(body,pos,len(body),out)
print('\n'.join(out))
