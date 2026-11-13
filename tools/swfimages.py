# Extrait les bitmaps d'un SWF (DefineBits*, DefineBitsLossless*) et vérifie qu'ils ne sont pas vides.
import sys, zlib, struct, os, io, json
from PIL import Image
def tags(path):
    b=open(path,'rb').read()
    body=zlib.decompress(b[8:]) if b[:3]==b'CWS' else b[8:]
    nb=body[0]>>3; rl=(5+4*nb+7)//8; pos=rl+4
    while pos<len(body):
        th=struct.unpack('<H',body[pos:pos+2])[0];code=th>>6;ln=th&63;pos+=2
        if ln==63: ln=struct.unpack('<I',body[pos:pos+4])[0];pos+=4
        yield code, body[pos:pos+ln]
        if code==0: break
        pos+=ln
def lossless(code,d):
    cid,fmt,w,h=struct.unpack('<HBHH',d[:7]); alpha=code==36
    if fmt==3:
        n=d[7]+1; raw=zlib.decompress(d[8:]); cs=4 if alpha else 3
        pal=raw[:n*cs]; pitch=(w+3)&~3; px=raw[n*cs:]
        im=Image.new('RGBA',(w,h))
        out=[]
        for y in range(h):
            for x in range(w):
                i=px[y*pitch+x]; c=pal[i*cs:i*cs+cs]
                out.append((c[0],c[1],c[2],c[3] if alpha else 255) if i<n else (0,0,0,0))
        im.putdata(out); return cid,im
    raw=zlib.decompress(d[7:])
    if fmt==5:
        im=Image.frombytes('RGBA',(w,h),raw,'raw','ARGB')
        if alpha: # prémultiplié
            px=[(min(255,r*255//a) if a else 0,min(255,g*255//a) if a else 0,min(255,b*255//a) if a else 0,a) for r,g,b,a in im.getdata()]
            im.putdata(px)
        else:
            im=im.convert('RGB').convert('RGBA')
        return cid,im
    if fmt==4:
        pitch=((w*2)+3)&~3; im=Image.new('RGBA',(w,h)); out=[]
        for y in range(h):
            for x in range(w):
                v=struct.unpack('>H',raw[y*pitch+2*x:y*pitch+2*x+2])[0]
                out.append((((v>>10)&31)<<3,((v>>5)&31)<<3,(v&31)<<3,255))
        im.putdata(out); return cid,im
    raise ValueError('fmt %d'%fmt)
def jpeg(code,d,tables):
    cid=struct.unpack('<H',d[:2])[0]
    if code==6: data=tables[:-2]+d[2:][2:] if tables else d[2:]
    elif code==21: data=d[2:]
    else:
        off=struct.unpack('<I',d[2:6])[0]; data=d[6:6+off]; adata=d[6+off:]
    data=data.replace(b'\xff\xd9\xff\xd8',b'')
    im=Image.open(io.BytesIO(data)); im.load(); im=im.convert('RGBA')
    if code==35 and adata:
        a=zlib.decompress(adata); im.putalpha(Image.frombytes('L',im.size,a))
    return cid,im
def main(path,out):
    os.makedirs(out,exist_ok=True); tables=None; rep=[]
    for code,d in tags(path):
        try:
            if code==8: tables=d; continue
            if code in (20,36): cid,im=lossless(code,d)
            elif code in (6,21,35): cid,im=jpeg(code,d,tables)
            else: continue
        except Exception as e:
            rep.append({'tag':code,'err':str(e)}); continue
        a=im.getchannel('A'); ex=a.getextrema(); bbox=im.getbbox()
        colors=len(set(im.convert('RGB').getdata())) if im.width*im.height<300000 else -1
        ok = ex[1]>0 and im.width>0 and im.height>0 and (colors!=1 or ex[1]>0)
        f=os.path.join(out,'bmp_%d.png'%cid); im.save(f)
        rep.append({'id':cid,'w':im.width,'h':im.height,'alphaMax':ex[1],'colors':colors,'ok':bool(ok and bbox)})
    return rep
if __name__=='__main__':
    r=main(sys.argv[1],sys.argv[2]); print(json.dumps(r))
