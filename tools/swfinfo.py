import sys, zlib, lzma, struct, os, json
def info(p):
    b=open(p,'rb').read()
    if len(b)<8: return {'err':'tiny'}
    sig=b[:3]; ver=b[3]
    try:
        if sig==b'FWS': body=b[8:]
        elif sig==b'CWS': body=zlib.decompressobj().decompress(b[8:])
        elif sig==b'ZWS': body=lzma.LZMADecompressor(format=lzma.FORMAT_RAW,filters=[{'id':lzma.FILTER_LZMA1,'dict_size':1<<24}]).decompress(b[17:]) if False else None
        else: return {'err':'notswf','sig':sig.hex()}
    except Exception as e: return {'err':str(e)[:40],'v':ver}
    if body is None: return {'v':ver,'zws':1}
    nbits=body[0]>>3; rl=(5+4*nbits+7)//8
    rect=int.from_bytes(body[:rl],'big'); 
    vals=[]; tot=5+4*nbits; 
    for i in range(4): vals.append((rect>>(tot-5-nbits*(i+1)) & ((1<<nbits)-1)))
    w=(vals[1]-vals[0])//20; h=(vals[3]-vals[2])//20
    fr=body[rl+1]+body[rl]/256; frames=struct.unpack('<H',body[rl+2:rl+4])[0]
    pos=rl+4; as3=False; tags={}; 
    while pos+2<=len(body):
        th=struct.unpack('<H',body[pos:pos+2])[0]; code=th>>6; ln=th&63; pos+=2
        if ln==63: ln=struct.unpack('<I',body[pos:pos+4])[0]; pos+=4
        if code==69: as3=bool(body[pos]&8)
        tags[code]=tags.get(code,0)+1
        pos+=ln
        if code==0: break
    abc= tags.get(82,0)+tags.get(72,0)
    act= tags.get(12,0)+tags.get(59,0)+tags.get(26,0)
    snd= tags.get(14,0); bmp=sum(tags.get(c,0) for c in (6,21,35,36,20,90))
    return {'v':ver,'w':w,'h':h,'fps':round(fr,1),'frames':frames,'as3':as3 or abc>0,'doAction':tags.get(12,0)+tags.get(59,0),'sounds':snd,'bitmaps':bmp,'shapes':sum(tags.get(c,0) for c in (2,22,32,83)),'sprites':tags.get(39,0)}
for p in sys.argv[1:]:
    print(json.dumps({'p':p,**info(p)}))
