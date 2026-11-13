import sys, zlib, struct, io, os, json, re
from PIL import Image
def load(p):
    b=open(p,'rb').read()
    body=zlib.decompress(b[8:]) if b[:3]==b'CWS' else b[8:]
    nb=body[0]>>3; rl=(5+4*nb+7)//8
    fps=body[rl+1]+body[rl]/256; frames=struct.unpack('<H',body[rl+2:rl+4])[0]
    return b[3],body,rl+4,fps,frames
def tags(body,pos,end):
    while pos+2<=end:
        th=struct.unpack('<H',body[pos:pos+2])[0]; code=th>>6; ln=th&63; pos+=2
        if ln==63: ln=struct.unpack('<I',body[pos:pos+4])[0]; pos+=4
        yield code,pos,ln
        pos+=ln
        if code==0: break
def fixjpeg(d):
    d=d.replace(b'\xff\xd9\xff\xd8',b'')
    if d[:4]==b'\xff\xd9\xff\xd8': d=d[4:]
    return d
def stat(im):
    im=im.convert('RGBA'); a=im.getchannel('A')
    ex=a.getextrema(); 
    if ex[1]==0: return 'transparent'
    rgb=im.convert('RGB'); e=rgb.getextrema()
    if all(lo==hi for lo,hi in e) and ex[0]==ex[1]: return 'uniforme'
    return 'ok'
def run(p,outdir):
    ver,body,pos,fps,frames=load(p)
    res={'file':os.path.basename(p),'ver':ver,'fps':round(fps,2),'frames':frames,'bitmaps':[],'sounds':[],'streams':0,'refs':set()}
    jt=None
    os.makedirs(outdir,exist_ok=True)
    def walk(s,e):
        nonlocal jt
        for code,p0,ln in tags(body,s,e):
            d=body[p0:p0+ln]
            if code==39: walk(p0+4,p0+ln); continue
            if code==8: jt=d
            if code==18 or code==45: res['streams']+=1
            if code==14:
                cid=struct.unpack('<H',d[:2])[0]; f=d[2]; fmt=['raw','adpcm','mp3','raw-le','nelly16','nelly8','nelly','?','?','?','?','speex'][f>>4]
                n=struct.unpack('<I',d[3:7])[0]; rate=[5512,11025,22050,44100][(f>>2)&3]
                res['sounds'].append({'id':cid,'fmt':fmt,'rate':rate,'samples':n,'sec':round(n/rate,2)})
            if code in (6,21,35,20,36):
                cid=struct.unpack('<H',d[:2])[0]; info={'id':cid,'tag':code}
                try:
                    if code in (6,21,35):
                        if code==35:
                            off=struct.unpack('<I',d[2:6])[0]; jd=d[6:6+off]; alpha=zlib.decompress(d[6+off:])
                        else: jd=d[2:]; alpha=None
                        if code==6 and jt: jd=jt[:-2]+jd[2:]
                        if jd[:8]==b'\x89PNG\r\n\x1a\n' or jd[:3]==b'GIF': im=Image.open(io.BytesIO(jd))
                        else: im=Image.open(io.BytesIO(fixjpeg(jd)))
                        im.load()
                        if alpha is not None and len(alpha)>=im.size[0]*im.size[1]:
                            im=im.convert('RGB'); im.putalpha(Image.frombytes('L',im.size,alpha[:im.size[0]*im.size[1]]))
                    else:
                        fmt=d[2]; w,h=struct.unpack('<HH',d[3:7])
                        if fmt==3:
                            n=d[7]+1; z=zlib.decompress(d[8:]); cs=4 if code==36 else 3
                            pal=z[:n*cs]; stride=(w+3)&~3; px=z[n*cs:]
                            im=Image.new('RGBA',(w,h)); pp=im.load()
                            for y in range(h):
                                for x in range(w):
                                    i=px[y*stride+x]; c=pal[i*cs:i*cs+cs]
                                    pp[x,y]=(c[0],c[1],c[2],c[3] if cs==4 else 255)
                        elif fmt==5:
                            z=zlib.decompress(d[7:]); im=Image.frombytes('RGBA',(w,h),z[:w*h*4],'raw','ARGB')
                            if code==20: im.putalpha(255)
                        else:
                            z=zlib.decompress(d[7:]); info['fmt']=fmt; im=None
                    if im is not None:
                        info['size']=im.size; info['state']=stat(im)
                        im.save(os.path.join(outdir,'bmp_%d.png'%cid))
                    else: info['state']='format15'
                except Exception as ex:
                    info['state']='erreur:'+str(ex)[:60]
                res['bitmaps'].append(info)
            if code in (12,59):
                for m in re.finditer(rb'[\w./-]+\.(?:swf|mp3|xml|php|png|jpg)',d): res['refs'].add(m.group().decode('latin1'))
    walk(pos,len(body))
    res['refs']=sorted(res['refs'])
    return res
out=[]
for p in sys.argv[2:]:
    try: out.append(run(p,os.path.join(sys.argv[1],os.path.basename(p))))
    except Exception as e: out.append({'file':p,'err':str(e)})
print(json.dumps(out))
