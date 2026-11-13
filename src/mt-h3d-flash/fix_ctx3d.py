# Remplace les constantes des énumérations Stage3D (absentes de Ruffle) par leur valeur chaîne.
import re, sys, os
def camel(s):
    p = s.lower().split('_')
    return p[0] + ''.join(x.capitalize() for x in p[1:])
special = {'BYTES_4':'bytes4','FLOAT_1':'float1','FLOAT_2':'float2','FLOAT_3':'float3','FLOAT_4':'float4','BGRA':'bgra','MIPLINEAR':'miplinear','MIPNEAREST':'mipnearest','MIPNONE':'mipnone'}
pat = re.compile(r'(?:flash\.display3D\.)?(Context3D(?:BlendFactor|BufferUsage|CompareMode|MipFilter|Profile|ProgramType|TextureFilter|TextureFormat|TriangleFace|VertexBufferFormat|WrapMode))\.([A-Z_0-9]+)\b')
n = 0
for root in sys.argv[1:]:
    for dp, _, fs in os.walk(root):
        for f in fs:
            if not f.endswith('.hx'): continue
            p = os.path.join(dp, f); s = open(p, encoding='latin-1', newline='').read()
            s2, k = pat.subn(lambda m: 'cast "%s"' % special.get(m.group(2), camel(m.group(2))), s)
            if k:
                n += k; open(p, 'w', encoding='latin-1', newline='').write(s2)
print(n, 'constantes remplacées')
